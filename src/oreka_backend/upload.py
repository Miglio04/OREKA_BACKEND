import io
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import pymupdf  # PyMuPDF
from fastapi import HTTPException, UploadFile
from oreka_backend.kpi_calculations import kpi_pos_only
from oreka_backend.models import POSLine


class FileProcessor:
    """Handles processing of uploaded CSV and PDF files."""

    def __init__(self, storage_dir: str = "uploads"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    async def process_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Process uploaded file (CSV or PDF) and return structured data.

        Args:
            file: Uploaded file from FastAPI

        Returns:
            Dict containing processed data and metadata
        """
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        file_extension = file.filename.lower().split(".")[-1]

        if file_extension == "csv":
            return await self._process_csv(file)
        elif file_extension == "pdf":
            return await self._process_pdf(file)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Only CSV and PDF files are supported.",
            )

    async def _process_csv(self, file: UploadFile) -> Dict[str, Any]:
        """Process CSV file (assumed to be Cachier machine export)."""
        try:
            contents = await file.read()

            # Try different encodings
            for encoding in ["utf-8", "latin-1", "iso-8859-1"]:
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise HTTPException(status_code=400, detail="Could not decode CSV file")

            # Convert DataFrame to records
            records = df.to_dict("records")

            # Clean up NaN values
            cleaned_records = []
            for record in records:
                cleaned_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        cleaned_record[key] = None
                    else:
                        cleaned_record[key] = value
                cleaned_records.append(cleaned_record)

            processed_data = {
                "file_type": "csv",
                "file_name": file.filename,
                "processed_at": datetime.now().isoformat(),
                "total_records": len(cleaned_records),
                "columns": list(df.columns),
                "data": cleaned_records,
            }

            # Save to JSON
            self._save_to_json(processed_data)

            return processed_data

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing CSV: {str(e)}"
            )

    async def _process_pdf(self, file: UploadFile) -> Dict[str, Any]:
        """Process PDF file (assumed to be an invoice)."""
        try:
            contents = await file.read()

            # Open PDF document
            doc = pymupdf.open(stream=contents, filetype="pdf")

            extracted_data = {"pages": [], "text_content": "", "metadata": {}}

            # Extract text from each page
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                extracted_data["pages"].append({
                    "page_number": page_num + 1,
                    "text": text,
                })
                extracted_data["text_content"] += text + "\n"

            # Extract basic invoice information
            invoice_info = self._extract_invoice_info(extracted_data["text_content"])

            processed_data = {
                "file_type": "pdf",
                "file_name": file.filename,
                "processed_at": datetime.now().isoformat(),
                "page_count": len(doc),
                "invoice_info": invoice_info,
                "raw_data": extracted_data,
            }

            # Close document
            doc.close()

            # Save to JSON
            self._save_to_json(processed_data)

            return processed_data

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error processing PDF: {str(e)}"
            )

    def _extract_invoice_info(self, text: str) -> Dict[str, Any]:
        """Extract basic invoice information from PDF text."""
        invoice_info = {}

        # Try to extract common invoice fields
        patterns = {
            "invoice_number": r"(?:invoice|factur[ae]?|rechnung)\s*#?\s*:?\s*([A-Z0-9\-]+)",
            "date": r"(?:date|datum|fecha)\s*:?\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            "total": r"(?:total|gesamt|summe|montant)\s*:?\s*([€$£]?\s*\d+[,.]?\d*)",
            "company": r"(?:^|\n)([A-Z][A-Za-z\s&.,]+(?:GmbH|Ltd|Inc|Corp|SA|SL))",
        }

        for field, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                invoice_info[field] = (
                    matches[0] if isinstance(matches[0], str) else matches[0]
                )

        return invoice_info

    def _save_to_json(self, data: Dict[str, Any]) -> str:
        """Save processed data to JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_type = data.get("file_type", "unknown")
        filename = f"{file_type}_{timestamp}.json"
        filepath = os.path.join(self.storage_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def get_all_processed_files(self) -> List[Dict[str, Any]]:
        """Retrieve all processed files from storage."""
        files = []

        if not os.path.exists(self.storage_dir):
            return files

        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        files.append(data)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")

        # Sort by processed_at timestamp (newest first)
        files.sort(key=lambda x: x.get("processed_at", ""), reverse=True)
        return files

    def get_computations_summary(self) -> Dict[str, Any]:
        """Generate summary of all computations and data."""
        files = self.get_all_processed_files()

        # Initialize summary with KPI structure
        summary = {
            "total_files": len(files),
            "file_types": {},
            "recent_files": [],
            "statistics": {},
            # KPI fields that frontend expects
            "revenue_total": 0,
            "revenue_by_area": {},
            "revenue_by_payment": {},
            "receipt_count": 0,
            "average_receipt": 0,
            "discount_rate": None,
        }

        csv_count = 0
        pdf_count = 0
        total_records = 0
        pos_lines = []

        for file_data in files:
            file_type = file_data.get("file_type", "unknown")

            if file_type == "csv":
                csv_count += 1
                total_records += file_data.get("total_records", 0)

                # Extract POS data for KPI calculations
                csv_data = file_data.get("data", [])
                for record in csv_data:
                    try:
                        # Convert the record to POSLine model
                        pos_line = POSLine(
                            timestamp=datetime.fromisoformat(
                                record["timestamp"].replace(" ", "T")
                            ),
                            item_type=record["item_type"],
                            item_name=record["item_name"],
                            quantity=int(record["quantity"]),
                            price_per_item=float(record["price_per_item"]),
                            total_price=float(record["total_price"]),
                            payment_method=record["payment_method"],
                            area=record["area"],
                            receipt_id=record["receipt_id"],
                        )
                        pos_lines.append(pos_line)
                    except (ValueError, KeyError, TypeError) as e:
                        # Skip invalid records
                        print(f"Skipping invalid record: {record}, Error: {e}")
                        continue

            elif file_type == "pdf":
                pdf_count += 1

        # Calculate KPIs from POS data
        if pos_lines:
            kpi_results = kpi_pos_only(pos_lines)
            # Convert Decimal values to float for JSON serialization
            summary.update({
                "revenue_total": float(kpi_results.get("revenue_total", 0)),
                "revenue_by_area": {
                    k: float(v)
                    for k, v in kpi_results.get("revenue_by_area", {}).items()
                },
                "revenue_by_payment": {
                    k: float(v)
                    for k, v in kpi_results.get("revenue_by_payment", {}).items()
                },
                "receipt_count": kpi_results.get("receipt_count", 0),
                "average_receipt": float(kpi_results.get("average_receipt", 0)),
                "discount_rate": float(kpi_results["discount_rate"])
                if kpi_results.get("discount_rate") is not None
                else None,
            })

        summary["file_types"] = {"csv": csv_count, "pdf": pdf_count}

        summary["statistics"] = {
            "total_csv_records": total_records,
            "total_invoices": pdf_count,
        }

        # Get recent files (last 10)
        summary["recent_files"] = [
            {
                "file_name": f.get("file_name"),
                "file_type": f.get("file_type"),
                "processed_at": f.get("processed_at"),
                "records": f.get("total_records")
                if f.get("file_type") == "csv"
                else f.get("page_count"),
            }
            for f in files[:10]
        ]

        return summary

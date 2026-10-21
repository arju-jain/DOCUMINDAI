import csv
import os
from pathlib import Path
import pymupdf

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "evaluation" / "dataset"
GROUND_TRUTH_CSV = BASE_DIR / "evaluation" / "ground_truth.csv"

DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Define 32 diverse, realistic ground-truth invoice specifications
INVOICE_SPECS = [
    {
        "id": "DOC-001",
        "filename": "inv_01_techcorp.pdf",
        "vendor_name": "TechCorp Solutions Inc",
        "invoice_number": "TC-2026-881",
        "invoice_date": "2026-05-14",
        "subtotal": 1250.00,
        "tax": 125.00,
        "grand_total": 1375.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-002",
        "filename": "inv_02_apex_logistics.pdf",
        "vendor_name": "Apex Global Logistics",
        "invoice_number": "AGL-99401",
        "invoice_date": "2026-06-20",
        "subtotal": 3400.00,
        "tax": 340.00,
        "grand_total": 3740.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-003",
        "filename": "inv_03_summit_cloud.png",
        "vendor_name": "Summit Cloud Systems",
        "invoice_number": "SC-10024",
        "invoice_date": "2026-07-01",
        "subtotal": 520.00,
        "tax": 52.00,
        "grand_total": 572.00,
        "format": "png",
        "type": "image",
    },
    {
        "id": "DOC-004",
        "filename": "inv_04_blue_ocean_retail.pdf",
        "vendor_name": "Blue Ocean Retailers",
        "invoice_number": "BOR-4421",
        "invoice_date": "2026-04-18",
        "subtotal": 890.50,
        "tax": 89.05,
        "grand_total": 979.55,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-005",
        "filename": "inv_05_quantum_lab.jpg",
        "vendor_name": "Quantum Research Labs",
        "invoice_number": "QRL-7730",
        "invoice_date": "2026-08-11",
        "subtotal": 2100.00,
        "tax": 210.00,
        "grand_total": 2310.00,
        "format": "jpg",
        "type": "image",
    },
    {
        "id": "DOC-006",
        "filename": "inv_06_stellar_media.pdf",
        "vendor_name": "Stellar Media Partners",
        "invoice_number": "SMP-00892",
        "invoice_date": "2026-03-25",
        "subtotal": 1500.00,
        "tax": 150.00,
        "grand_total": 1650.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-007",
        "filename": "inv_07_horizon_energy.pdf",
        "vendor_name": "Horizon Clean Energy",
        "invoice_number": "HCE-3312",
        "invoice_date": "2026-09-05",
        "subtotal": 4500.00,
        "tax": 450.00,
        "grand_total": 4950.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-008",
        "filename": "inv_08_nexus_consulting.png",
        "vendor_name": "Nexus Strategic Advisory",
        "invoice_number": "NSA-5510",
        "invoice_date": "2026-02-19",
        "subtotal": 6000.00,
        "tax": 600.00,
        "grand_total": 6600.00,
        "format": "png",
        "type": "image",
    },
    {
        "id": "DOC-009",
        "filename": "inv_09_vanguard_security.pdf",
        "vendor_name": "Vanguard Cyber Security",
        "invoice_number": "VCS-9021",
        "invoice_date": "2026-10-02",
        "subtotal": 1850.00,
        "tax": 185.00,
        "grand_total": 2035.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-010",
        "filename": "inv_10_zenith_supplies.pdf",
        "vendor_name": "Zenith Medical Supplies",
        "invoice_number": "ZMS-6644",
        "invoice_date": "2026-01-30",
        "subtotal": 920.00,
        "tax": 92.00,
        "grand_total": 1012.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-011",
        "filename": "inv_11_silverline_logistics.jpg",
        "vendor_name": "Silverline Freightways",
        "invoice_number": "SLF-1029",
        "invoice_date": "2026-05-22",
        "subtotal": 3100.00,
        "tax": 310.00,
        "grand_total": 3410.00,
        "format": "jpg",
        "type": "image",
    },
    {
        "id": "DOC-012",
        "filename": "inv_12_crestview_print.pdf",
        "vendor_name": "Crestview Creative Print",
        "invoice_number": "CCP-4011",
        "invoice_date": "2026-06-15",
        "subtotal": 740.00,
        "tax": 74.00,
        "grand_total": 814.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-013",
        "filename": "inv_13_pinnacle_soft.pdf",
        "vendor_name": "Pinnacle Software Labs",
        "invoice_number": "PSL-8820",
        "invoice_date": "2026-07-28",
        "subtotal": 2800.00,
        "tax": 280.00,
        "grand_total": 3080.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-014",
        "filename": "inv_14_aurora_design.png",
        "vendor_name": "Aurora Industrial Design",
        "invoice_number": "AID-5541",
        "invoice_date": "2026-08-04",
        "subtotal": 1950.00,
        "tax": 195.00,
        "grand_total": 2145.00,
        "format": "png",
        "type": "image",
    },
    {
        "id": "DOC-015",
        "filename": "inv_15_beacon_telecom.pdf",
        "vendor_name": "Beacon Telecom Network",
        "invoice_number": "BTN-9923",
        "invoice_date": "2026-09-18",
        "subtotal": 420.00,
        "tax": 42.00,
        "grand_total": 462.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-016",
        "filename": "inv_16_emerald_catering.pdf",
        "vendor_name": "Emerald Events & Catering",
        "invoice_number": "EEC-3341",
        "invoice_date": "2026-03-12",
        "subtotal": 1350.00,
        "tax": 135.00,
        "grand_total": 1485.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-017",
        "filename": "inv_17_omega_hardware.jpg",
        "vendor_name": "Omega Computer Systems",
        "invoice_number": "OCS-7712",
        "invoice_date": "2026-04-05",
        "subtotal": 3800.00,
        "tax": 380.00,
        "grand_total": 4180.00,
        "format": "jpg",
        "type": "image",
    },
    {
        "id": "DOC-018",
        "filename": "inv_18_solaris_legal.pdf",
        "vendor_name": "Solaris Legal Counsel",
        "invoice_number": "SLC-1190",
        "invoice_date": "2026-05-30",
        "subtotal": 5500.00,
        "tax": 550.00,
        "grand_total": 6050.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-019",
        "filename": "inv_19_prime_packaging.pdf",
        "vendor_name": "Prime Industrial Pack",
        "invoice_number": "PIP-6632",
        "invoice_date": "2026-06-08",
        "subtotal": 850.00,
        "tax": 85.00,
        "grand_total": 935.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-020",
        "filename": "inv_20_matrix_automation.png",
        "vendor_name": "Matrix Automation Group",
        "invoice_number": "MAG-8841",
        "invoice_date": "2026-07-14",
        "subtotal": 4900.00,
        "tax": 490.00,
        "grand_total": 5390.00,
        "format": "png",
        "type": "image",
    },
    {
        "id": "DOC-021",
        "filename": "inv_21_atlas_freight.pdf",
        "vendor_name": "Atlas Freight Express",
        "invoice_number": "AFE-2204",
        "invoice_date": "2026-08-26",
        "subtotal": 1600.00,
        "tax": 160.00,
        "grand_total": 1760.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-022",
        "filename": "inv_22_falcon_electrical.pdf",
        "vendor_name": "Falcon Electrical Works",
        "invoice_number": "FEW-5509",
        "invoice_date": "2026-09-10",
        "subtotal": 2250.00,
        "tax": 225.00,
        "grand_total": 2475.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-023",
        "filename": "inv_23_titan_security.jpg",
        "vendor_name": "Titan Facility Services",
        "invoice_number": "TFS-4419",
        "invoice_date": "2026-10-08",
        "subtotal": 3150.00,
        "tax": 315.00,
        "grand_total": 3465.00,
        "format": "jpg",
        "type": "image",
    },
    {
        "id": "DOC-024",
        "filename": "inv_24_clarity_analytics.pdf",
        "vendor_name": "Clarity Data Analytics",
        "invoice_number": "CDA-9981",
        "invoice_date": "2026-01-17",
        "subtotal": 2700.00,
        "tax": 270.00,
        "grand_total": 2970.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-025",
        "filename": "inv_25_evergreen_landscaping.pdf",
        "vendor_name": "Evergreen Landscape Co",
        "invoice_number": "ELC-3382",
        "invoice_date": "2026-02-24",
        "subtotal": 680.00,
        "tax": 68.00,
        "grand_total": 748.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-026",
        "filename": "inv_26_phoenix_robotics.png",
        "vendor_name": "Phoenix Robotics Corp",
        "invoice_number": "PRC-7729",
        "invoice_date": "2026-03-19",
        "subtotal": 7500.00,
        "tax": 750.00,
        "grand_total": 8250.00,
        "format": "png",
        "type": "image",
    },
    {
        "id": "DOC-027",
        "filename": "inv_27_mercury_shipping.pdf",
        "vendor_name": "Mercury Marine Shipping",
        "invoice_number": "MMS-1154",
        "invoice_date": "2026-04-29",
        "subtotal": 4100.00,
        "tax": 410.00,
        "grand_total": 4510.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-028",
        "filename": "inv_28_polaris_consult.pdf",
        "vendor_name": "Polaris Financial Advisory",
        "invoice_number": "PFA-6691",
        "invoice_date": "2026-05-09",
        "subtotal": 3500.00,
        "tax": 350.00,
        "grand_total": 3850.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-029",
        "filename": "inv_29_cascade_beverage.jpg",
        "vendor_name": "Cascade Beverage Distributors",
        "invoice_number": "CBD-2287",
        "invoice_date": "2026-06-18",
        "subtotal": 1120.00,
        "tax": 112.00,
        "grand_total": 1232.00,
        "format": "jpg",
        "type": "image",
    },
    {
        "id": "DOC-030",
        "filename": "inv_30_vortex_engineering.pdf",
        "vendor_name": "Vortex Engineering Works",
        "invoice_number": "VEW-8876",
        "invoice_date": "2026-07-22",
        "subtotal": 5800.00,
        "tax": 580.00,
        "grand_total": 6380.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-031",
        "filename": "inv_31_radiant_clean.pdf",
        "vendor_name": "Radiant Facility Cleaners",
        "invoice_number": "RFC-4490",
        "invoice_date": "2026-08-15",
        "subtotal": 650.00,
        "tax": 65.00,
        "grand_total": 715.00,
        "format": "pdf",
        "type": "digital",
    },
    {
        "id": "DOC-032",
        "filename": "inv_32_stratus_hosting.pdf",
        "vendor_name": "Stratus Hosting Cloud",
        "invoice_number": "SHC-9905",
        "invoice_date": "2026-09-29",
        "subtotal": 980.00,
        "tax": 98.00,
        "grand_total": 1078.00,
        "format": "pdf",
        "type": "digital",
    },
]


def generate_document_file(spec: dict) -> Path:
    """Generates an authentic PDF or image invoice matching the spec."""
    file_path = DATASET_DIR / spec["filename"]
    
    # Text template
    doc_text = f"""
{spec['vendor_name']}
Corporate Headquarters, Suite 400
Industrial District, Business Bay

INVOICE

Invoice Number: {spec['invoice_number']}
Invoice Date: {spec['invoice_date']}
Payment Due: Net 30 Days

Billed To:
Enterprise Client Partner Corp
789 Market Boulevard, Floor 12

Line Items:
1. Professional Technology Services    Qty: 1    Rate: {spec['subtotal']:.2f}    Amount: {spec['subtotal']:.2f}

Financial Breakdown:
Subtotal: ${spec['subtotal']:.2f}
Tax: ${spec['tax']:.2f}
Grand Total: ${spec['grand_total']:.2f}

Thank you for your business!
For electronic wire inquiries: wire@billing.internal
"""

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 70), doc_text.strip(), fontsize=11)

    if spec["format"] == "pdf":
        doc.save(str(file_path))
        doc.close()
    elif spec["format"] in ("png", "jpg"):
        # Render page to image pixmap
        pix = page.get_pixmap(dpi=150)
        if spec["format"] == "png":
            pix.save(str(file_path))
        else:
            # Save as jpg
            pix.pil_save(str(file_path), format="JPEG")
        doc.close()

    return file_path


def main():
    print(f"Generating 32 held-out evaluation documents in {DATASET_DIR}...")
    
    # 1. Generate files
    for spec in INVOICE_SPECS:
        path = generate_document_file(spec)
        print(f"  Created: {path.name} ({spec['format'].upper()})")

    # 2. Write ground_truth.csv
    with open(GROUND_TRUTH_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "document_id",
            "filename",
            "vendor_name",
            "invoice_number",
            "invoice_date",
            "subtotal",
            "tax",
            "grand_total",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for spec in INVOICE_SPECS:
            writer.writerow({
                "document_id": spec["id"],
                "filename": spec["filename"],
                "vendor_name": spec["vendor_name"],
                "invoice_number": spec["invoice_number"],
                "invoice_date": spec["invoice_date"],
                "subtotal": f"{spec['subtotal']:.2f}",
                "tax": f"{spec['tax']:.2f}",
                "grand_total": f"{spec['grand_total']:.2f}",
            })

    print(f"\nGround truth successfully written to {GROUND_TRUTH_CSV}")
    print(f"Total documents: {len(INVOICE_SPECS)}")


if __name__ == "__main__":
    main()

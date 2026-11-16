from pathlib import Path
import json, random
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "contracts"
OUT.mkdir(parents=True, exist_ok=True)

suppliers = [
    ("CleanCo","Facilities"),("BrightClean","Facilities"),("GreenFacilities","Facilities"),
    ("PrimeMaintenance","Facilities"),("OfficeCare","Facilities"),("TechPro","IT"),
    ("SecureIT","IT"),("CloudBridge","IT"),("DataWorks","IT"),("NetSupport","IT"),
    ("FastMove","Logistics"),("NorthStarLogistics","Logistics"),("SwiftFreight","Logistics"),
    ("RoadRunner","Logistics"),("CargoPlus","Logistics"),("BlueSkyIT","IT"),
    ("MetroFacilities","Facilities"),("RapidDelivery","Logistics"),("CoreSystems","IT"),
    ("UrbanClean","Facilities"),("ApexSupport","IT"),("FleetLine","Logistics"),
    ("VertexTech","IT"),("EvergreenFM","Facilities"),("PioneerCargo","Logistics"),
    ("NexaCloud","IT"),("TotalCare","Facilities"),("TransGlobal","Logistics"),
    ("BrightByte","IT"),("UnityServices","Facilities"),("SilverRoute","Logistics"),
    ("OrionIT","IT")
]
styles = getSampleStyleSheet()

def build_one(i, supplier, category):
    # Dates are deliberately varied so Q1 2027 and date-filter questions return useful results.
    end_month = [1,2,3,4,6,9,12][i % 7]
    end_day = [15,28,31,30,30,30,31][i % 7]
    end_day = min(end_day, 28) if end_month == 2 else end_day
    end_date = f"2027-{end_month:02d}-{end_day:02d}"
    start_date = f"2026-{(i%6)+1:02d}-01"
    value = 25000 + i * 2750
    auto = (i % 4 != 1)
    notice = [30,60,90,120][i % 4]
    contract_id = f"contract-{i+1:03d}"
    filename = f"{supplier.replace(' ','_')}_{category}.pdf"
    path = OUT / filename

    story = [
        Paragraph(f"<b>{supplier} – {category} Supplier Contract</b>", styles["Title"]),
        Paragraph(f"Supplier: {supplier}", styles["BodyText"]),
        Paragraph(f"Category: {category}", styles["BodyText"]),
        Paragraph(f"Start Date: {start_date}", styles["BodyText"]),
        Paragraph(f"End Date: {end_date}", styles["BodyText"]),
        Paragraph(f"Contract Value: £{value:,.2f}", styles["BodyText"]),
        Paragraph(f"Auto Renew: {'Yes' if auto else 'No'}", styles["BodyText"]),
        Paragraph(f"Notice Period: {notice} days", styles["BodyText"]),
        Spacer(1, 8*mm),
        Paragraph("CLAUSE 1 – SERVICES AND SCOPE", styles["Heading2"]),
        Paragraph(f"The supplier {supplier} will provide professional {category.lower()} services in accordance with this agreement. The supplier must maintain suitably trained staff, records and service continuity throughout the contract term.", styles["BodyText"]),
        Paragraph("CLAUSE 5 – RENEWAL", styles["Heading2"]),
        Paragraph(
            (f"This agreement automatically renews for a further 12-month period unless either party gives at least {notice} days written notice before the end date. The current contract end date is {end_date}.")
            if auto else
            (f"This agreement does not automatically renew. Any extension must be agreed in writing by both parties before the end date {end_date}.")
            , styles["BodyText"]),
        Paragraph("CLAUSE 8 – SERVICE LEVEL AGREEMENT (SLA)", styles["Heading2"]),
        Paragraph("The following service levels apply. The table below is an integral part of this clause and must be read as a whole.", styles["BodyText"]),
        Table([
            ["Service measure","Target","Measurement","Service credit / penalty"],
            ["Response time","95% within target","Monthly","£500 per missed target"],
            ["Service availability","99.5%","Monthly","£750 per 0.5% below target"],
            ["Issue resolution","90% within agreed time","Monthly","£300 per missed target"],
        ], colWidths=[42*mm,35*mm,30*mm,55*mm]),
        Paragraph("CLAUSE 12 – TERMINATION", styles["Heading2"]),
        Paragraph(f"Either party may terminate this agreement by providing {notice} days written notice to the other party, subject to any outstanding obligations. Material breach may be subject to a 30-day remediation period.", styles["BodyText"]),
        Paragraph("CLAUSE 14 – FEES AND PAYMENT", styles["Heading2"]),
        Paragraph(f"The annual contract value is £{value:,.2f}. Invoices are payable within 30 days of receipt. Disputed invoices must be raised in writing.", styles["BodyText"]),
        Paragraph("CLAUSE 16 – GOVERNING LAW", styles["Heading2"]),
        Paragraph("This synthetic demonstration agreement is governed by the laws of England and Wales. It is fictional and must not be used as a real legal contract.", styles["BodyText"]),
    ]
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=16*mm, bottomMargin=16*mm)
    doc.build(story)
    meta = {"contract_id": contract_id, "supplier": supplier, "category": category,
            "start_date": start_date, "end_date": end_date, "contract_value": value,
            "auto_renew": auto, "notice_days": notice}
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    return filename

if __name__ == "__main__":
    random.seed(7)
    for i, (supplier, category) in enumerate(suppliers):
        build_one(i, supplier, category)
    print(f"Generated {len(suppliers)} synthetic contracts in {OUT}")

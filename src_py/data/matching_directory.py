"""
Business directory of bank commercial banking clients available for distress recovery matching.
"""
from typing import Dict
from src_py.models.matching_schemas import BusinessEntityProfile, BusinessRole

BANK_BUSINESS_DIRECTORY: Dict[str, BusinessEntityProfile] = {
    "CUST_MSME_TIRUPPUR_001": BusinessEntityProfile(
        customer_id="CUST_MSME_TIRUPPUR_001",
        company_name="Sri Balaji Fabrics & Knits Pvt Ltd",
        is_distressed=True,
        distress_reason="Low knitwear order volume & idle Machine C capacity (-35% MoM)",
        role=BusinessRole.SUPPLIER,
        industry="Textiles & Apparel",
        sub_sectors=["Knitwear", "Terry Fabric", "Single Jersey"],
        products_services=["Combed Cotton Yarn Fabric", "Terry Knitted Rolls", "Custom Bleached Knit Fabric"],
        cluster_region="Tiruppur",
        city="Tiruppur",
        state="Tamil Nadu",
        annual_turnover=32000000.0,
        business_size="SMALL",
        capacity_units_per_month=35000.0,  # 35,000 kg fabric/month (currently running at 45%)
        demand_units_per_month=0.0,
        target_partner_types=["Garment Manufacturer", "Apparel Exporter", "Retail Sourcing Brand"],
        immediate_requirement_description="Seeking off-take orders for 15,000 kg/month idle circular knitting capacity"
    ),
    "CUST_CORP_GARMENT_TIR_009": BusinessEntityProfile(
        customer_id="CUST_CORP_GARMENT_TIR_009",
        company_name="Apex Global Apparel Export Corporation",
        is_distressed=False,
        role=BusinessRole.BUYER,
        industry="Textiles & Apparel",
        sub_sectors=["Apparel Export", "Garmenting", "Ready-Made Garments"],
        products_services=["Men's T-Shirts", "Athleisure", "Knitted Polo Shirts"],
        cluster_region="Tiruppur",
        city="Tiruppur",
        state="Tamil Nadu",
        annual_turnover=185000000.0,
        business_size="MEDIUM",
        capacity_units_per_month=0.0,
        demand_units_per_month=18000.0,  # Needs 18,000 kg high-grade single jersey/terry fabric/month
        target_partner_types=["Knitted Fabric Supplier", "Fabric Dyeing Mill"],
        immediate_requirement_description="Urgent procurement requirement for 16,000 kg/month OEKO-TEX certified combed knit fabric for European export order"
    ),
    "CUST_TEMP_LIQ_004": BusinessEntityProfile(
        customer_id="CUST_TEMP_LIQ_004",
        company_name="Kaveri Precision Tools LLP",
        is_distressed=True,
        distress_reason="Delayed receivables and 40% idle 5-axis CNC capacity",
        role=BusinessRole.SUPPLIER,
        industry="Precision Engineering & Auto Ancillary",
        sub_sectors=["CNC Milling", "Bicycle Components", "Auto Gears"],
        products_services=["High-Precision Gears", "Bicycle Hub Shafts", "Tooling Dies"],
        cluster_region="Ludhiana",
        city="Ludhiana",
        state="Punjab",
        annual_turnover=18000000.0,
        business_size="SMALL",
        capacity_units_per_month=5000.0,
        demand_units_per_month=0.0,
        target_partner_types=["OEM Manufacturer", "Tier-1 Auto Component Assembler"],
        immediate_requirement_description="Job-work contracting for precision 5-axis CNC milling"
    ),
    "CUST_AUTO_OEM_LUDH_014": BusinessEntityProfile(
        customer_id="CUST_AUTO_OEM_LUDH_014",
        company_name="Hero Cycle Allied Heavy Engineering Ltd",
        is_distressed=False,
        role=BusinessRole.BUYER,
        industry="Precision Engineering & Auto Ancillary",
        sub_sectors=["Bicycle Manufacturing", "Light EV Chassis"],
        products_services=["Bicycles", "Cargo E-Trikes"],
        cluster_region="Ludhiana",
        city="Ludhiana",
        state="Punjab",
        annual_turnover=450000000.0,
        business_size="CORPORATE",
        capacity_units_per_month=0.0,
        demand_units_per_month=4500.0,
        target_partner_types=["Precision Toolmaker", "Machining Contractor"],
        immediate_requirement_description="Sourcing local Tier-2 machining vendor for precision hub shafts"
    )
}

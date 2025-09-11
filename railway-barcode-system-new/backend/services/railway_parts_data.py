# backend/services/railway_parts_data.py
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class RailwayPartSpecification:
    """Comprehensive specifications for railway track fittings"""
    # Basic Information
    part_name: str
    part_code: str
    rdso_specification: str

    # Material Properties
    material: str
    material_grade: str
    hardness_hrc: str
    tensile_strength_mpa: int
    yield_strength_mpa: int

    # Physical Dimensions
    dimensions: Dict[str, float]
    weight_kg: float
    tolerance: str

    # Performance Characteristics
    service_life_years: int
    load_capacity_kn: float
    fatigue_cycles: int
    temperature_range: str

    # Quality Standards
    is_standard: List[str]
    testing_requirements: List[str]
    inspection_frequency: str

    # Environmental Resistance
    corrosion_resistance: str
    uv_resistance: str
    chemical_resistance: List[str]

    # Installation & Maintenance
    installation_torque_nm: Optional[float]
    maintenance_interval_months: int
    replacement_indicators: List[str]

    # Cost & Procurement
    approximate_cost_inr: str
    procurement_lead_time_weeks: int
    approved_suppliers: List[str]


class RailwayPartsDatabase:
    """Database of Indian Railway standard parts specifications"""

    def __init__(self):
        self.parts_catalog = self._initialize_parts_catalog()

    def _initialize_parts_catalog(self) -> Dict[str, RailwayPartSpecification]:
        """Initialize comprehensive parts database"""
        return {
            "elastic_rail_clip": RailwayPartSpecification(
                part_name="Elastic Rail Clip (ERC)",
                part_code="ERC-MK-III/MK-V",
                rdso_specification="RDSO/T-3707",

                material="Spring Steel",
                material_grade="60Si2MnA / 60Si2CrA",
                hardness_hrc="42-48 HRC",
                tensile_strength_mpa=1600,
                yield_strength_mpa=1400,

                dimensions={
                    "length_mm": 180.0,
                    "width_mm": 85.0,
                    "diameter_mm": 13.0,
                    "clip_height_mm": 45.0
                },
                weight_kg=0.52,
                tolerance="±0.5mm",

                service_life_years=25,
                load_capacity_kn=17.0,
                fatigue_cycles=5000000,
                temperature_range="-20°C to +65°C",

                is_standard=["IS:5680", "BS:EN 13481-3", "AREMA"],
                testing_requirements=[
                    "Toe load test (10-17 kN)",
                    "Fatigue test (5M cycles)",
                    "Corrosion resistance test",
                    "Dimensional inspection",
                    "Hardness verification"
                ],
                inspection_frequency="Every 12 months",

                corrosion_resistance="Hot dip galvanized coating (>85 microns)",
                uv_resistance="Excellent (outdoor rated)",
                chemical_resistance=["De-icing salts", "Industrial pollutants", "Acid rain"],

                installation_torque_nm=None,
                maintenance_interval_months=12,
                replacement_indicators=[
                    "Toe load below 10 kN",
                    "Visible cracks or deformation",
                    "Excessive corrosion (>20% thickness loss)",
                    "Clip dislodgement frequency >2/year"
                ],

                approximate_cost_inr="₹180-250 per piece",
                procurement_lead_time_weeks=8,
                approved_suppliers=["Pandrol India", "Vossloh Cogifer", "SAIL"],
            ),

            "rail_pad": RailwayPartSpecification(
                part_name="Grooved Rubber Sole Plate (GRSP)",
                part_code="GRSP/CGRSP",
                rdso_specification="RDSO/T-3708",

                material="Natural Rubber Compound",
                material_grade="NR/SBR Blend (Shore A 60±5)",
                hardness_hrc="60±5 Shore A",
                tensile_strength_mpa=18,
                yield_strength_mpa=12,

                dimensions={
                    "length_mm": 200.0,
                    "width_mm": 170.0,
                    "thickness_mm": 6.5,
                    "groove_depth_mm": 2.5,
                },
                weight_kg=0.28,
                tolerance="±1.0mm thickness",

                service_life_years=8,
                load_capacity_kn=25.0,
                fatigue_cycles=2000000,
                temperature_range="-40°C to +70°C",

                is_standard=["IS:13450", "BS:EN 13146-9", "UIC 864-5"],
                testing_requirements=[
                    "Static stiffness test",
                    "Dynamic stiffness test",
                    "Fatigue test (2M cycles)",
                    "Creep resistance test",
                    "Ozone aging test",
                ],
                inspection_frequency="Every 6 months",

                corrosion_resistance="N/A (Rubber material)",
                uv_resistance="Good with carbon black protection",
                chemical_resistance=["Oils", "Greases", "Track lubricants"],

                installation_torque_nm=None,
                maintenance_interval_months=6,
                replacement_indicators=[
                    "Thickness reduction >15%",
                    "Cracking or splitting",
                    "Permanent set >2mm",
                    "Loss of elasticity",
                ],

                approximate_cost_inr="₹85-120 per piece",
                procurement_lead_time_weeks=6,
                approved_suppliers=["Escorts Railway", "Texmaco Rail", "BEML"],
            ),

            "liner": RailwayPartSpecification(
                part_name="Insulating Liner",
                part_code="GFN-66/HVN Liner",
                rdso_specification="RDSO/T-3709",

                material="Glass Filled Nylon (GFN-66) / HVN",
                material_grade="PA66-GF30",
                hardness_hrc="Shore D 80±5",
                tensile_strength_mpa=160,
                yield_strength_mpa=120,

                dimensions={
                    "length_mm": 165.0,
                    "width_mm": 95.0,
                    "thickness_mm": 10.0,
                    "rail_groove_width_mm": 75.0,
                },
                weight_kg=0.15,
                tolerance="±0.2mm",

                service_life_years=15,
                load_capacity_kn=20.0,
                fatigue_cycles=3000000,
                temperature_range="-30°C to +80°C",

                is_standard=["RDSO Spec", "IEC 62631-3-1", "ASTM D6109"],
                testing_requirements=[
                    "Electrical insulation test (>1MΩ)",
                    "Mechanical strength test",
                    "UV aging test",
                    "Dimensional stability test",
                    "Water absorption test",
                ],
                inspection_frequency="Every 18 months",

                corrosion_resistance="N/A (Non-metallic)",
                uv_resistance="Excellent with UV stabilizers",
                chemical_resistance=["Acids", "Alkalis", "Track chemicals"],

                installation_torque_nm=None,
                maintenance_interval_months=18,
                replacement_indicators=[
                    "Cracking or chipping",
                    "Loss of electrical insulation (<1MΩ)",
                    "Dimensional changes >±1mm",
                    "Color change indicating UV damage",
                ],

                approximate_cost_inr="₹95-140 per piece",
                procurement_lead_time_weeks=10,
                approved_suppliers=["RDSO Approved Vendors", "Lewis Berger", "Kemrock"],
            ),

            "sleeper": RailwayPartSpecification(
                part_name="Pre-stressed Concrete Sleeper",
                part_code="PSC Sleeper Type VIII",
                rdso_specification="RDSO/T-2012",

                material="Pre-stressed Concrete",
                material_grade="M-50 Grade Concrete",
                hardness_hrc="N/A",
                tensile_strength_mpa=5,
                yield_strength_mpa=45,  # Compressive

                dimensions={
                    "length_mm": 2740.0,
                    "width_mm": 254.0,
                    "height_mm": 200.0,
                    "rail_seat_spacing_mm": 1676.0,
                },
                weight_kg=285.0,
                tolerance="±5mm length, ±2mm other dimensions",

                service_life_years=50,
                load_capacity_kn=350.0,
                fatigue_cycles=10000000,
                temperature_range="-20°C to +65°C",

                is_standard=["IS:13687", "BS:EN 13230", "UIC 713R"],
                testing_requirements=[
                    "Positive moment test",
                    "Negative moment test",
                    "Rail seat load test",
                    "Dynamic load test",
                    "Fatigue test",
                ],
                inspection_frequency="Every 24 months",

                corrosion_resistance="Excellent (alkaline concrete environment)",
                uv_resistance="Good",
                chemical_resistance=["De-icing chemicals", "Industrial atmosphere"],

                installation_torque_nm=None,
                maintenance_interval_months=24,
                replacement_indicators=[
                    "Cracking >0.2mm width",
                    "Spalling at rail seat",
                    "Loss of pre-stress",
                    "Dimensional deformation",
                ],

                approximate_cost_inr="₹3,500-4,200 per sleeper",
                procurement_lead_time_weeks=12,
                approved_suppliers=["L&T", "Tata Projects", "KCP", "SAIL"],
            ),
        }

    def get_part_specifications(self, part_type: str) -> Optional[RailwayPartSpecification]:
        """Get comprehensive specifications for a railway part"""
        return self.parts_catalog.get(part_type)

    def get_all_parts(self) -> Dict[str, RailwayPartSpecification]:
        """Get all parts specifications"""
        return self.parts_catalog

    def search_parts_by_specification(self, spec_number: str) -> List[RailwayPartSpecification]:
        """Search parts by RDSO specification number"""
        return [part for part in self.parts_catalog.values() if spec_number in part.rdso_specification]


# Initialize global parts database
railway_parts_db = RailwayPartsDatabase()

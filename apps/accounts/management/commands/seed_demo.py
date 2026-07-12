from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cases.models import Case, MOTagOption
from apps.stations.coast_stations import COAST_STATIONS, COUNTY_STATION_COUNTS, REGION
from apps.stations.models import PoliceStation

User = get_user_model()

MO_TAGS = [
    ("target", "residential", "Residential", 3),
    ("target", "commercial", "Commercial", 3),
    ("target", "vehicle", "Vehicle", 2),
    ("entry", "window", "Window Smash", 4),
    ("entry", "door_force", "Forced Door", 4),
    ("entry", "unlocked", "Unlocked Entry", 2),
    ("weapon", "bladed", "Bladed Tool", 5),
    ("weapon", "firearm", "Firearm", 5),
    ("weapon", "none", "No Weapon", 1),
    ("timeframe", "night", "Night (22:00–05:00)", 2),
    ("timeframe", "day", "Daytime", 1),
    ("escape", "foot", "On Foot", 2),
    ("escape", "vehicle", "Motor Vehicle", 3),
]

# Sample cases across counties for demo analytics and MO cross-matching
DEMO_CASES = [
    ("MSA-MVT", "CR-2026-001", "Burglary at Old Town residential compound", "theft", "Old Town, Mvita", {"target": "residential", "entry": "window", "weapon": "bladed", "timeframe": "night"}),
    ("MSA-NYL", "CR-2026-002", "Hotel store break-in, Beach Road Nyali", "theft", "Beach Road, Nyali", {"target": "commercial", "entry": "window", "weapon": "bladed", "timeframe": "night", "escape": "foot"}),
    ("MSA-CHG", "CR-2026-003", "Cargo theft at Port Reitz yard", "theft", "Port Reitz, Changamwe", {"target": "commercial", "entry": "door_force", "weapon": "none", "timeframe": "night"}),
    ("MSA-LKN", "CR-2026-004", "Vehicle break-in near Likoni Ferry", "theft", "Likoni Channel Road", {"target": "vehicle", "entry": "window", "weapon": "none", "timeframe": "day"}),
    ("MSA-BMB", "CR-2026-005", "Shanzu road residential burglary", "theft", "Bamburi Beach", {"target": "residential", "entry": "window", "weapon": "bladed", "timeframe": "night"}),
    ("KLF-KIL", "CR-2026-006", "Residential window entry, Kilifi Township", "theft", "Bofa Road, Kilifi", {"target": "residential", "entry": "window", "weapon": "bladed", "timeframe": "night"}),
    ("KLF-MLD", "CR-2026-007", "Shop robbery on Lamu Road Malindi", "robbery", "Lamu Road, Malindi", {"target": "commercial", "entry": "door_force", "weapon": "firearm", "timeframe": "night", "escape": "foot"}),
    ("KLF-MTP", "CR-2026-008", "Mtwapa nightclub district theft", "theft", "Mtwapa Town", {"target": "commercial", "entry": "window", "weapon": "bladed", "timeframe": "night", "escape": "foot"}),
    ("KLF-WTM", "CR-2026-009", "Watamu villa break-in", "theft", "Watamu Beach", {"target": "residential", "entry": "window", "weapon": "none", "timeframe": "night"}),
    ("KWL-DNA", "CR-2026-010", "Diani Beach resort store robbery", "robbery", "Diani Beach Road", {"target": "commercial", "entry": "window", "weapon": "bladed", "timeframe": "night", "escape": "foot"}),
    ("KWL-MSB", "CR-2026-011", "Msambweni market stall theft", "theft", "Msambweni Market", {"target": "commercial", "entry": "unlocked", "weapon": "none", "timeframe": "day"}),
    ("KWL-MTG", "CR-2026-012", "Matuga residential assault", "assault", "Matuga Township", {"target": "residential", "entry": "unlocked", "weapon": "bladed", "timeframe": "night"}),
    ("LAM-LAM", "CR-2026-013", "Heritage shop break-in Lamu Old Town", "robbery", "Lamu Old Town", {"target": "commercial", "entry": "window", "weapon": "bladed", "timeframe": "night", "escape": "foot"}),
    ("LAM-MPK", "CR-2026-014", "Mpeketoni trading centre theft", "theft", "Mpeketoni", {"target": "commercial", "entry": "window", "weapon": "bladed", "timeframe": "night"}),
    ("TTV-VOI", "CR-2026-015", "Warehouse theft Mombasa Highway Voi", "theft", "Mombasa Road, Voi", {"target": "commercial", "entry": "door_force", "weapon": "none", "timeframe": "night"}),
    ("TTV-TVT", "CR-2026-016", "Border town shop robbery Taveta", "robbery", "Taveta Town", {"target": "commercial", "entry": "door_force", "weapon": "firearm", "timeframe": "day"}),
    ("TTV-WDY", "CR-2026-017", "Wundanyi hillside residential burglary", "theft", "Wundanyi Town", {"target": "residential", "entry": "window", "weapon": "none", "timeframe": "night"}),
    ("TNR-HOL", "CR-2026-018", "Residential assault Hola township", "assault", "Hola Township", {"target": "residential", "entry": "unlocked", "weapon": "bladed", "timeframe": "night"}),
    ("TNR-BUR", "CR-2026-019", "Livestock theft report Bura", "theft", "Bura Township", {"target": "commercial", "entry": "unlocked", "weapon": "none", "timeframe": "night"}),
    ("TNR-MDG", "CR-2026-020", "Madogo highway vehicle theft", "theft", "Madogo Town", {"target": "vehicle", "entry": "window", "weapon": "none", "timeframe": "day"}),
    ("KLF-MLD", "CR-2026-021", "Silversand residential burglary", "theft", "Silversand, Malindi", {"target": "residential", "entry": "window", "weapon": "none", "timeframe": "night"}),
    ("MSA-MVT", "CR-2026-022", "Moi Avenue shop front robbery", "robbery", "Moi Avenue, Mvita", {"target": "commercial", "entry": "window", "weapon": "bladed", "timeframe": "night", "escape": "foot"}),
]

OFFICERS = [
    ("officer1", "CR-MSA-1001", "MSA-MVT", "Hassan", "Mwachari"),
    ("officer2", "CR-MSA-1002", "MSA-NYL", "Fatuma", "Bakari"),
    ("officer3", "CR-KLF-1003", "KLF-KIL", "James", "Katana"),
    ("officer4", "CR-KWL-1004", "KWL-DNA", "Amina", "Mwaringa"),
    ("officer5", "CR-LAM-1005", "LAM-LAM", "Omar", "Abubakar"),
    ("officer6", "CR-TTV-1006", "TTV-VOI", "Grace", "Mghanga"),
    ("officer7", "CR-TNR-1007", "TNR-HOL", "Yusuf", "Hirsi"),
]


class Command(BaseCommand):
    help = "Seed Coast Region police stations (all known counties) and demo cases."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="Lexguard123!",
            help="Password to assign to every seeded demo officer and commander.",
        )

    def handle(self, *args, **options):
        password = options["password"]

        for category, value, label, weight in MO_TAGS:
            MOTagOption.objects.update_or_create(
                category=category,
                value=value,
                defaults={"label": label, "weight": weight, "is_active": True},
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(MO_TAGS)} MO tag options"))

        active_codes = {row[0] for row in COAST_STATIONS}
        PoliceStation.objects.exclude(code__in=active_codes).update(is_active=False)

        station_map = {}
        for code, name, county, sub_county in COAST_STATIONS:
            station, _ = PoliceStation.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "region": REGION,
                    "county": county,
                    "sub_county": sub_county,
                    "is_active": True,
                },
            )
            station_map[code] = station

        self.stdout.write(self.style.SUCCESS(f"Registered {len(COAST_STATIONS)} Coast Region stations:"))
        for county, count in sorted(COUNTY_STATION_COUNTS.items()):
            self.stdout.write(f"  {county}: {count} stations")

        officer_map = {}
        for username, badge, station_code, first, last in OFFICERS:
            user, created = User.objects.update_or_create(
                username=username,
                defaults={
                    "badge_number": badge,
                    "email": f"{username}@lexguard.coast.go.ke",
                    "role": User.Role.OFFICER,
                    "station": station_map[station_code],
                    "first_name": first,
                    "last_name": last,
                    "must_change_password": False,
                },
            )
            user.set_password(password)
            user.save(update_fields=["password"])
            officer_map[station_code] = user

        commander, created = User.objects.update_or_create(
            username="commander",
            defaults={
                "badge_number": "CR-CMD-01",
                "email": "command@lexguard.coast.go.ke",
                "role": User.Role.COMMANDER,
                "first_name": "Ali",
                "last_name": "Kombo",
                "must_change_password": False,
            },
        )
        commander.set_password(password)
        commander.save(update_fields=["password"])

        default_officer = officer_map["MSA-MVT"]
        for station_code, case_number, title, category, location, mo in DEMO_CASES:
            station = station_map[station_code]
            Case.objects.update_or_create(
                station=station,
                case_number=case_number,
                defaults={
                    "title": title,
                    "crime_category": category,
                    "location": location,
                    "narrative": (
                        f"Incident reported at {location}, {station.county} County, {REGION} Region. "
                        f"{station.name} opened regional case file {case_number}."
                    ),
                    "status": "open",
                    "modus_operandi": mo,
                    "created_by": officer_map.get(station_code, default_officer),
                    "opened_at": timezone.now(),
                },
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DEMO_CASES)} demo cases across {len(COUNTY_STATION_COUNTS)} counties."))
        for username, _badge, station_code, first, last in OFFICERS:
            st = station_map[station_code]
            self.stdout.write(f"  Officer ({st.county}): {username} / {password}  ({st.code})")
        self.stdout.write(f"  Regional Commander: commander / {password}")

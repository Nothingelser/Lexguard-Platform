"""Known police stations across Kenya's Coast Region (six counties).

Sources: Kenya Gazette (2020 gazetted stations), National Police Service
divisional listings, and published OCPD station directories.
"""

REGION = "Coast"

# (code, official_name, county, sub_county)
COAST_STATIONS = [
    # —— Mombasa County ——
    ("MSA-MVT", "Mombasa Central Police Station", "Mombasa", "Mvita"),
    ("MSA-MBR", "Mbaraki Lines Police Station", "Mombasa", "Mvita"),
    ("MSA-TNK", "Tononoka Police Station", "Mombasa", "Mvita"),
    ("MSA-MKP", "Makupa Police Station", "Mombasa", "Mvita"),
    ("MSA-CHG", "Changamwe Police Station", "Mombasa", "Changamwe"),
    ("MSA-PRZ", "Port Reitz Police Station", "Mombasa", "Changamwe"),
    ("MSA-NYL", "Nyali Police Station", "Mombasa", "Nyali"),
    ("MSA-SNZ", "Shanzu Police Station", "Mombasa", "Nyali"),
    ("MSA-BMB", "Bamburi Police Station", "Mombasa", "Kisauni"),
    ("MSA-KIS", "Kisauni Police Station", "Mombasa", "Kisauni"),
    ("MSA-LKN", "Likoni Police Station", "Mombasa", "Likoni"),
    ("MSA-JOM", "Jomvu Police Station", "Mombasa", "Jomvu"),
    # —— Kilifi County ——
    ("KLF-KIL", "Kilifi Police Station", "Kilifi", "Kilifi South"),
    ("KLF-MLD", "Malindi Police Station", "Kilifi", "Malindi"),
    ("KLF-WTM", "Watamu Police Station", "Kilifi", "Malindi"),
    ("KLF-MRK", "Mariakani Police Station", "Kilifi", "Kaloleni"),
    ("KLF-MTP", "Mtwapa Police Station", "Kilifi", "Kilifi North"),
    ("KLF-KJP", "Kijipwa Police Station", "Kilifi", "Kilifi North"),
    ("KLF-KLN", "Kaloleni Police Station", "Kilifi", "Kaloleni"),
    ("KLF-GNG", "Gongoni Police Station", "Kilifi", "Magarini"),
    ("KLF-NGR", "Ngerenya Police Station", "Kilifi", "Kilifi North"),
    ("KLF-MTS", "Matsangoni Police Station", "Kilifi", "Kilifi North"),
    ("KLF-RAB", "Rabai Police Station", "Kilifi", "Rabai"),
    ("KLF-GNZ", "Ganze Police Station", "Kilifi", "Ganze"),
    # —— Kwale County ——
    ("KWL-KWL", "Kwale Police Station", "Kwale", "Kwale"),
    ("KWL-DNA", "Diani Police Station", "Kwale", "Msambweni"),
    ("KWL-MSB", "Msambweni Police Station", "Kwale", "Msambweni"),
    ("KWL-UKD", "Ukunda Police Station", "Kwale", "Msambweni"),
    ("KWL-MTG", "Matuga Police Station", "Kwale", "Matuga"),
    ("KWL-MMB", "Mamba Police Station", "Kwale", "Matuga"),
    ("KWL-KNG", "Kinango Police Station", "Kwale", "Kinango"),
    ("KWL-LUG", "Lungalunga Police Station", "Kwale", "Lungalunga"),
    # —— Lamu County ——
    ("LAM-LAM", "Lamu Police Station", "Lamu", "Lamu West"),
    ("LAM-MKW", "Mokowe Police Station", "Lamu", "Lamu East"),
    ("LAM-HND", "Hindi Police Station", "Lamu", "Lamu West"),
    ("LAM-FZA", "Faza Police Station", "Lamu", "Lamu East"),
    ("LAM-KGW", "Kiangwe Police Station", "Lamu", "Lamu West"),
    ("LAM-MPK", "Mpeketoni Police Station", "Lamu", "Lamu West"),
    ("LAM-WIO", "Witu Police Station", "Lamu", "Lamu West"),
    ("LAM-BAS", "Basuba Police Station", "Lamu", "Lamu East"),
    # —— Taita Taveta County ——
    ("TTV-VOI", "Voi Police Station", "Taita Taveta", "Voi"),
    ("TTV-TVT", "Taveta Police Station", "Taita Taveta", "Taveta"),
    ("TTV-WDY", "Wundanyi Police Station", "Taita Taveta", "Wundanyi"),
    ("TTV-MNG", "Maungu Police Station", "Taita Taveta", "Voi"),
    ("TTV-KSG", "Kasigau Police Station", "Taita Taveta", "Voi"),
    ("TTV-TAU", "Tausa Police Station", "Taita Taveta", "Voi"),
    ("TTV-MWT", "Mwatate Police Station", "Taita Taveta", "Mwatate"),
    ("TTV-MKT", "Maktau Police Station", "Taita Taveta", "Taveta"),
    ("TTV-KTB", "Kitobo Police Station", "Taita Taveta", "Taveta"),
    ("TTV-CHM", "Chumvini Police Station", "Taita Taveta", "Taveta"),
    ("TTV-MHN", "Mhange Police Station", "Taita Taveta", "Wundanyi"),
    ("TTV-KSH", "Kishushe Police Station", "Taita Taveta", "Wundanyi"),
    # —— Tana River County ——
    ("TNR-HOL", "Hola Police Station", "Tana River", "Galole"),
    ("TNR-BUR", "Bura Police Station", "Tana River", "Bura"),
    ("TNR-MDG", "Madogo Police Station", "Tana River", "Garsen"),
    ("TNR-TRS", "Tarasaa Police Station", "Tana River", "Tana Delta"),
    ("TNR-MNZ", "Mnazini Police Station", "Tana River", "Tana Delta"),
    ("TNR-WLD", "Waldena Police Station", "Tana River", "Tana River"),
    ("TNR-CHK", "Chardende Police Station", "Tana River", "Tana North"),
    ("TNR-ASK", "Asako Police Station", "Tana River", "Tana North"),
]

COUNTY_STATION_COUNTS = {}
for _code, _name, county, _sc in COAST_STATIONS:
    COUNTY_STATION_COUNTS[county] = COUNTY_STATION_COUNTS.get(county, 0) + 1

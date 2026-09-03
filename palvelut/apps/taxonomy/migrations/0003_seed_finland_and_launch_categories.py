from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q


REGIONS = (
    ("01", "Uusimaa"),
    ("02", "Southwest Finland"),
    ("04", "Satakunta"),
    ("05", "Kanta-Häme"),
    ("06", "Pirkanmaa"),
    ("07", "Päijät-Häme"),
    ("08", "Kymenlaakso"),
    ("09", "South Karelia"),
    ("10", "South Savo"),
    ("11", "North Savo"),
    ("12", "North Karelia"),
    ("13", "Central Finland"),
    ("14", "South Ostrobothnia"),
    ("15", "Ostrobothnia"),
    ("16", "Central Ostrobothnia"),
    ("17", "North Ostrobothnia"),
    ("18", "Kainuu"),
    ("19", "Lapland"),
    ("21", "Åland"),
)

# Statistics Finland, Municipalities 2026 and municipality→region correspondence,
# valid from 2026-01-01. Municipality codes are the official three-digit codes.
MUNICIPALITIES = (
    ("020", "Akaa", "06"), ("005", "Alajärvi", "14"),
    ("009", "Alavieska", "17"), ("010", "Alavus", "14"),
    ("016", "Asikkala", "07"), ("018", "Askola", "01"),
    ("019", "Aura", "02"), ("035", "Brändö", "21"),
    ("043", "Eckerö", "21"), ("046", "Enonkoski", "10"),
    ("047", "Enontekiö", "19"), ("049", "Espoo", "01"),
    ("050", "Eura", "04"), ("051", "Eurajoki", "04"),
    ("052", "Evijärvi", "14"), ("060", "Finström", "21"),
    ("061", "Forssa", "05"), ("062", "Föglö", "21"),
    ("065", "Geta", "21"), ("069", "Haapajärvi", "17"),
    ("071", "Haapavesi", "17"), ("072", "Hailuoto", "17"),
    ("074", "Halsua", "16"), ("075", "Hamina", "08"),
    ("076", "Hammarland", "21"), ("077", "Hankasalmi", "13"),
    ("078", "Hanko", "01"), ("079", "Harjavalta", "04"),
    ("081", "Hartola", "07"), ("082", "Hattula", "05"),
    ("086", "Hausjärvi", "05"), ("111", "Heinola", "07"),
    ("090", "Heinävesi", "12"), ("091", "Helsinki", "01"),
    ("097", "Hirvensalmi", "10"), ("098", "Hollola", "07"),
    ("102", "Huittinen", "04"), ("103", "Humppila", "05"),
    ("105", "Hyrynsalmi", "18"), ("106", "Hyvinkää", "01"),
    ("108", "Hämeenkyrö", "06"), ("109", "Hämeenlinna", "05"),
    ("139", "Ii", "17"), ("140", "Iisalmi", "11"),
    ("142", "Iitti", "07"), ("143", "Ikaalinen", "06"),
    ("145", "Ilmajoki", "14"), ("146", "Ilomantsi", "12"),
    ("153", "Imatra", "09"), ("148", "Inari", "19"),
    ("149", "Ingå", "01"), ("151", "Isojoki", "14"),
    ("152", "Isokyrö", "14"), ("165", "Janakkala", "05"),
    ("167", "Joensuu", "12"), ("169", "Jokioinen", "05"),
    ("170", "Jomala", "21"), ("171", "Joroinen", "11"),
    ("172", "Joutsa", "13"), ("176", "Juuka", "12"),
    ("177", "Juupajoki", "06"), ("178", "Juva", "10"),
    ("179", "Jyväskylä", "13"), ("181", "Jämijärvi", "04"),
    ("182", "Jämsä", "13"), ("186", "Järvenpää", "01"),
    ("202", "Kaarina", "02"), ("204", "Kaavi", "11"),
    ("205", "Kajaani", "18"), ("208", "Kalajoki", "17"),
    ("211", "Kangasala", "06"), ("213", "Kangasniemi", "10"),
    ("214", "Kankaanpää", "04"), ("216", "Kannonkoski", "13"),
    ("217", "Kannus", "16"), ("218", "Karijoki", "14"),
    ("224", "Karkkila", "01"), ("226", "Karstula", "13"),
    ("230", "Karvia", "04"), ("231", "Kaskinen", "15"),
    ("232", "Kauhajoki", "14"), ("233", "Kauhava", "14"),
    ("235", "Kauniainen", "01"), ("236", "Kaustinen", "16"),
    ("239", "Keitele", "11"), ("240", "Kemi", "19"),
    ("320", "Kemijärvi", "19"), ("241", "Keminmaa", "19"),
    ("322", "Kimitoön", "02"), ("244", "Kempele", "17"),
    ("245", "Kerava", "01"), ("249", "Keuruu", "13"),
    ("250", "Kihniö", "06"), ("256", "Kinnula", "13"),
    ("257", "Kirkkonummi", "01"), ("260", "Kitee", "12"),
    ("261", "Kittilä", "19"), ("263", "Kiuruvesi", "11"),
    ("265", "Kivijärvi", "13"), ("271", "Kokemäki", "04"),
    ("272", "Kokkola", "16"), ("273", "Kolari", "19"),
    ("275", "Konnevesi", "13"), ("276", "Kontiolahti", "12"),
    ("280", "Korsnäs", "15"), ("284", "Koski Tl", "02"),
    ("285", "Kotka", "08"), ("286", "Kouvola", "08"),
    ("287", "Kristinestad", "15"), ("288", "Kronoby", "15"),
    ("290", "Kuhmo", "18"), ("291", "Kuhmoinen", "06"),
    ("295", "Kumlinge", "21"), ("297", "Kuopio", "11"),
    ("300", "Kuortane", "14"), ("301", "Kurikka", "14"),
    ("304", "Kustavi", "02"), ("305", "Kuusamo", "17"),
    ("312", "Kyyjärvi", "13"), ("316", "Kärkölä", "07"),
    ("317", "Kärsämäki", "17"), ("318", "Kökar", "21"),
    ("398", "Lahti", "07"), ("399", "Laihia", "15"),
    ("400", "Laitila", "02"), ("407", "Lapinjärvi", "01"),
    ("402", "Lapinlahti", "11"), ("403", "Lappajärvi", "14"),
    ("405", "Lappeenranta", "09"), ("408", "Lapua", "14"),
    ("410", "Laukaa", "13"), ("416", "Lemi", "09"),
    ("417", "Lemland", "21"), ("418", "Lempäälä", "06"),
    ("420", "Leppävirta", "11"), ("421", "Lestijärvi", "16"),
    ("422", "Lieksa", "12"), ("423", "Lieto", "02"),
    ("425", "Liminka", "17"), ("426", "Liperi", "12"),
    ("444", "Lohja", "01"), ("430", "Loimaa", "02"),
    ("433", "Loppi", "05"), ("434", "Loviisa", "01"),
    ("435", "Luhanka", "13"), ("436", "Lumijoki", "17"),
    ("438", "Lumparland", "21"), ("440", "Larsmo", "15"),
    ("441", "Luumäki", "09"), ("475", "Malax", "15"),
    ("478", "Mariehamn", "21"), ("480", "Marttila", "02"),
    ("481", "Masku", "02"), ("483", "Merijärvi", "17"),
    ("484", "Merikarvia", "04"), ("489", "Miehikkälä", "08"),
    ("491", "Mikkeli", "10"), ("494", "Muhos", "17"),
    ("495", "Multia", "13"), ("498", "Muonio", "19"),
    ("499", "Korsholm", "15"), ("500", "Muurame", "13"),
    ("503", "Mynämäki", "02"), ("504", "Myrskylä", "01"),
    ("505", "Mäntsälä", "01"), ("508", "Mänttä-Vilppula", "06"),
    ("507", "Mäntyharju", "10"), ("529", "Naantali", "02"),
    ("531", "Nakkila", "04"), ("535", "Nivala", "17"),
    ("536", "Nokia", "06"), ("538", "Nousiainen", "02"),
    ("541", "Nurmes", "12"), ("543", "Nurmijärvi", "01"),
    ("545", "Närpes", "15"), ("560", "Orimattila", "07"),
    ("561", "Oripää", "02"), ("562", "Orivesi", "06"),
    ("563", "Oulainen", "17"), ("564", "Oulu", "17"),
    ("309", "Outokumpu", "12"), ("576", "Padasjoki", "07"),
    ("577", "Paimio", "02"), ("578", "Paltamo", "18"),
    ("445", "Pargas", "02"), ("580", "Parikkala", "09"),
    ("581", "Parkano", "06"), ("599", "Pedersöre", "15"),
    ("583", "Pelkosenniemi", "19"), ("854", "Pello", "19"),
    ("584", "Perho", "16"), ("592", "Petäjävesi", "13"),
    ("593", "Pieksämäki", "10"), ("595", "Pielavesi", "11"),
    ("598", "Jakobstad", "15"), ("601", "Pihtipudas", "13"),
    ("604", "Pirkkala", "06"), ("607", "Polvijärvi", "12"),
    ("608", "Pomarkku", "04"), ("609", "Pori", "04"),
    ("611", "Pornainen", "01"), ("638", "Porvoo", "01"),
    ("614", "Posio", "19"), ("615", "Pudasjärvi", "17"),
    ("616", "Pukkila", "01"), ("619", "Punkalaidun", "06"),
    ("620", "Puolanka", "18"), ("623", "Puumala", "10"),
    ("624", "Pyhtää", "08"), ("625", "Pyhäjoki", "17"),
    ("626", "Pyhäjärvi", "17"), ("630", "Pyhäntä", "17"),
    ("631", "Pyhäranta", "02"), ("635", "Pälkäne", "06"),
    ("636", "Pöytyä", "02"), ("678", "Raahe", "17"),
    ("710", "Raseborg", "01"), ("680", "Raisio", "02"),
    ("681", "Rantasalmi", "10"), ("683", "Ranua", "19"),
    ("684", "Rauma", "04"), ("686", "Rautalampi", "11"),
    ("687", "Rautavaara", "11"), ("689", "Rautjärvi", "09"),
    ("691", "Reisjärvi", "17"), ("694", "Riihimäki", "05"),
    ("697", "Ristijärvi", "18"), ("698", "Rovaniemi", "19"),
    ("700", "Ruokolahti", "09"), ("702", "Ruovesi", "06"),
    ("704", "Rusko", "02"), ("707", "Rääkkylä", "12"),
    ("729", "Saarijärvi", "13"), ("732", "Salla", "19"),
    ("734", "Salo", "02"), ("736", "Saltvik", "21"),
    ("790", "Sastamala", "06"), ("738", "Sauvo", "02"),
    ("739", "Savitaipale", "09"), ("740", "Savonlinna", "10"),
    ("742", "Savukoski", "19"), ("743", "Seinäjoki", "14"),
    ("746", "Sievi", "17"), ("747", "Siikainen", "04"),
    ("748", "Siikajoki", "17"), ("791", "Siikalatva", "17"),
    ("749", "Siilinjärvi", "11"), ("751", "Simo", "19"),
    ("753", "Sipoo", "01"), ("755", "Siuntio", "01"),
    ("758", "Sodankylä", "19"), ("759", "Soini", "14"),
    ("761", "Somero", "02"), ("762", "Sonkajärvi", "11"),
    ("765", "Sotkamo", "18"), ("766", "Sottunga", "21"),
    ("768", "Sulkava", "10"), ("771", "Sund", "21"),
    ("777", "Suomussalmi", "18"), ("778", "Suonenjoki", "11"),
    ("781", "Sysmä", "07"), ("783", "Säkylä", "04"),
    ("831", "Taipalsaari", "09"), ("832", "Taivalkoski", "17"),
    ("833", "Taivassalo", "02"), ("834", "Tammela", "05"),
    ("837", "Tampere", "06"), ("844", "Tervo", "11"),
    ("845", "Tervola", "19"), ("846", "Teuva", "14"),
    ("848", "Tohmajärvi", "12"), ("849", "Toholampi", "16"),
    ("850", "Toivakka", "13"), ("851", "Tornio", "19"),
    ("853", "Turku", "02"), ("857", "Tuusniemi", "11"),
    ("858", "Tuusula", "01"), ("859", "Tyrnävä", "17"),
    ("886", "Ulvila", "04"), ("887", "Urjala", "06"),
    ("889", "Utajärvi", "17"), ("890", "Utsjoki", "19"),
    ("892", "Uurainen", "13"), ("893", "Nykarleby", "15"),
    ("895", "Uusikaupunki", "02"), ("785", "Vaala", "17"),
    ("905", "Vaasa", "15"), ("908", "Valkeakoski", "06"),
    ("092", "Vantaa", "01"), ("915", "Varkaus", "11"),
    ("918", "Vehmaa", "02"), ("921", "Vesanto", "11"),
    ("922", "Vesilahti", "06"), ("924", "Veteli", "16"),
    ("925", "Vieremä", "11"), ("927", "Vihti", "01"),
    ("931", "Viitasaari", "13"), ("934", "Vimpeli", "14"),
    ("935", "Virolahti", "08"), ("936", "Virrat", "06"),
    ("941", "Vårdö", "21"), ("946", "Vörå", "15"),
    ("976", "Ylitornio", "19"), ("977", "Ylivieska", "17"),
    ("980", "Ylöjärvi", "06"), ("981", "Ypäjä", "05"),
    ("989", "Ähtäri", "14"), ("992", "Äänekoski", "13"),
)

CATEGORIES = {
    "accounting": {
        "name": "Accounting",
        "labels": {"ru": "Бухгалтерия", "fi": "Kirjanpito", "en": "Accounting"},
        "synonyms": {
            "ru": ("бухгалтер", "бухгалтерские услуги"),
            "fi": ("kirjanpitäjä", "tilitoimisto"),
            "en": ("bookkeeping", "accountant"),
        },
    },
    "legal": {
        "name": "Legal services",
        "labels": {"ru": "Юридические услуги", "fi": "Lakipalvelut", "en": "Legal services"},
        "synonyms": {
            "ru": ("юрист", "адвокат"), "fi": ("juristi", "asianajaja"),
            "en": ("lawyer", "legal advice"),
        },
    },
    "car-repair": {
        "name": "Car repair",
        "labels": {"ru": "Автосервис", "fi": "Autokorjaamo", "en": "Car repair"},
        "synonyms": {
            "ru": ("ремонт автомобилей", "автомеханик"),
            "fi": ("auton korjaus", "automekaanikko"),
            "en": ("auto repair", "mechanic"),
        },
    },
    "renovation": {
        "name": "Renovation",
        "labels": {"ru": "Ремонт и отделка", "fi": "Remontointi", "en": "Renovation"},
        "synonyms": {
            "ru": ("ремонт квартиры", "строительные работы"),
            "fi": ("remontti", "rakennustyöt"),
            "en": ("home renovation", "remodeling"),
        },
    },
    "electrical": {
        "name": "Electrical services",
        "labels": {"ru": "Электромонтажные работы", "fi": "Sähkötyöt", "en": "Electrical services"},
        "synonyms": {
            "ru": ("электрик", "электромонтаж"),
            "fi": ("sähköasentaja", "sähköasennus"),
            "en": ("electrician", "electrical installation"),
        },
    },
    "plumbing": {
        "name": "Plumbing",
        "labels": {"ru": "Сантехнические работы", "fi": "Putkityöt", "en": "Plumbing"},
        "synonyms": {
            "ru": ("сантехник", "водопровод"), "fi": ("putkimies", "LVI"),
            "en": ("plumber", "pipework"),
        },
    },
    "psychology": {
        "name": "Psychology",
        "labels": {"ru": "Психолог", "fi": "Psykologi", "en": "Psychology"},
        "synonyms": {
            "ru": ("психологическая помощь", "консультация психолога"),
            "fi": ("psykologipalvelut", "keskusteluapu"),
            "en": ("psychologist", "psychological counselling"),
        },
    },
    "massage-physiotherapy": {
        "name": "Massage and physiotherapy",
        "labels": {
            "ru": "Массаж и физиотерапия", "fi": "Hieronta ja fysioterapia",
            "en": "Massage and physiotherapy",
        },
        "synonyms": {
            "ru": ("массажист", "физиотерапевт"),
            "fi": ("hieroja", "fysioterapeutti"),
            "en": ("massage therapist", "physiotherapist"),
        },
    },
}


def seed_taxonomy(apps, schema_editor):
    Country = apps.get_model("taxonomy", "Country")
    Region = apps.get_model("taxonomy", "Region")
    Municipality = apps.get_model("taxonomy", "Municipality")
    Category = apps.get_model("taxonomy", "Category")
    CategoryLabel = apps.get_model("taxonomy", "CategoryLabel")
    CategorySynonym = apps.get_model("taxonomy", "CategorySynonym")

    finland, _ = Country.objects.update_or_create(code="FI", defaults={"name": "Finland"})
    regions = {}
    for code, name in REGIONS:
        region, _ = Region.objects.update_or_create(
            country=finland, code=code, defaults={"name": name}
        )
        regions[code] = region

    for code, name, region_code in MUNICIPALITIES:
        Municipality.objects.update_or_create(
            region=regions[region_code], code=code, defaults={"name": name}
        )

    for slug, payload in CATEGORIES.items():
        category, _ = Category.objects.update_or_create(
            slug=slug, defaults={"name": payload["name"]}
        )
        for locale, label in payload["labels"].items():
            CategoryLabel.objects.update_or_create(
                category=category, locale=locale, defaults={"label": label}
            )
        for locale, values in payload["synonyms"].items():
            for value in values:
                CategorySynonym.objects.get_or_create(
                    category=category, locale=locale, value=value
                )


def unseed_taxonomy(apps, schema_editor):
    Category = apps.get_model("taxonomy", "Category")
    Country = apps.get_model("taxonomy", "Country")
    Category.objects.filter(slug__in=CATEGORIES).delete()
    Country.objects.filter(code="FI").delete()


class Migration(migrations.Migration):
    dependencies = [("taxonomy", "0002_category_language")]

    operations = [
        migrations.CreateModel(
            name="CategoryLabel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_default=models.Func(function="uuidv7"),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("locale", models.CharField(max_length=2)),
                ("label", models.CharField(max_length=120)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="labels",
                        to="taxonomy.category",
                    ),
                ),
            ],
            options={"ordering": ("category_id", "locale")},
        ),
        migrations.CreateModel(
            name="CategorySynonym",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        db_default=models.Func(function="uuidv7"),
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("locale", models.CharField(max_length=2)),
                ("value", models.CharField(max_length=120)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="synonyms",
                        to="taxonomy.category",
                    ),
                ),
            ],
            options={"ordering": ("category_id", "locale", "value")},
        ),
        migrations.AddConstraint(
            model_name="categorylabel",
            constraint=models.CheckConstraint(
                condition=Q(locale__in=("ru", "fi", "en")),
                name="taxonomy_category_label_supported_locale",
            ),
        ),
        migrations.AddConstraint(
            model_name="categorylabel",
            constraint=models.UniqueConstraint(
                fields=("category", "locale"),
                name="taxonomy_category_label_locale_unique",
            ),
        ),
        migrations.AddConstraint(
            model_name="categorysynonym",
            constraint=models.CheckConstraint(
                condition=Q(locale__in=("ru", "fi", "en")),
                name="taxonomy_category_synonym_supported_locale",
            ),
        ),
        migrations.AddConstraint(
            model_name="categorysynonym",
            constraint=models.UniqueConstraint(
                fields=("category", "locale", "value"),
                name="taxonomy_category_synonym_unique",
            ),
        ),
        migrations.RunPython(seed_taxonomy, unseed_taxonomy),
    ]

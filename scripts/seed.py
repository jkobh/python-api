from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.database import database
from app.models import Maschine, Standort
from app.repositories import kaffeebohnen, maschinen, standorte
from app.repositories.errors import NotFoundError
from app.schemas import KaffeebohneCreate, MaschineCreate, StandortCreate


@dataclass(frozen=True, slots=True)
class StandortSeed:
    name: str
    ort: str
    modell: str
    bohnen: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SeedReport:
    standorte: int = 0
    maschinen: int = 0
    kaffeebohnen: int = 0


KATALOG: tuple[StandortSeed, ...] = (
    StandortSeed(
        name="Rösterei Innenstadt",
        ort="Karlsruhe",
        modell="Barista Pro",
        bohnen=("Arabica", "Espresso Blend", "Decaf"),
    ),
    StandortSeed(
        name="Büro Nord",
        ort="Mannheim",
        modell="Magnifica S",
        bohnen=("Arabica", "House Blend", "Robusta", "Espresso Blend"),
    ),
    StandortSeed(
        name="Café am Markt",
        ort="Heidelberg",
        modell="Jura E8",
        bohnen=("Espresso Blend", "Arabica", "Decaf", "House Blend"),
    ),
    StandortSeed(
        name="Labor Süd",
        ort="Stuttgart",
        modell="De'Longhi Dinamica",
        bohnen=("Robusta", "Arabica", "House Blend"),
    ),
    StandortSeed(
        name="Azubi-Küche",
        ort="Pforzheim",
        modell="Siemens EQ6",
        bohnen=("House Blend", "Arabica", "Espresso Blend", "Decaf", "Robusta"),
    ),
)


def finde_standort(session: Session, eintrag: StandortSeed) -> Standort | None:
    for kandidat in standorte.list_all(session, eintrag.name, eintrag.ort):
        if kandidat.name == eintrag.name and kandidat.ort == eintrag.ort:
            return kandidat
    return None


def finde_maschine(session: Session, standort: Standort) -> Maschine | None:
    try:
        return maschinen.get_by_standort(session, standort.id)
    except NotFoundError:
        return None


def stelle_standort_sicher(session: Session, eintrag: StandortSeed) -> tuple[Standort, bool]:
    vorhandener = finde_standort(session, eintrag)
    if vorhandener is not None:
        return vorhandener, False
    neuer = standorte.create(session, StandortCreate(name=eintrag.name, ort=eintrag.ort))
    return neuer, True


def stelle_maschine_sicher(
    session: Session, standort: Standort, modell: str
) -> tuple[Maschine, bool]:
    vorhandene = finde_maschine(session, standort)
    if vorhandene is not None:
        return vorhandene, False
    neue = maschinen.create(session, standort.id, MaschineCreate(modell=modell))
    return neue, True


def ergaenze_bohnen(session: Session, maschine: Maschine, sorten: tuple[str, ...]) -> int:
    vorhandene = {
        bohne.sorte for bohne in kaffeebohnen.list_by_maschine(session, maschine.id, None)
    }
    fehlende = [sorte for sorte in sorten if sorte not in vorhandene]
    for sorte in fehlende:
        kaffeebohnen.create(session, maschine.id, KaffeebohneCreate(sorte=sorte))
    return len(fehlende)


def ergaenze_katalog(session: Session, katalog: tuple[StandortSeed, ...]) -> SeedReport:
    neue_standorte = neue_maschinen = neue_bohnen = 0

    for eintrag in katalog:
        standort, standort_ist_neu = stelle_standort_sicher(session, eintrag)
        maschine, maschine_ist_neu = stelle_maschine_sicher(session, standort, eintrag.modell)
        neue_standorte += standort_ist_neu
        neue_maschinen += maschine_ist_neu
        neue_bohnen += ergaenze_bohnen(session, maschine, eintrag.bohnen)

    return SeedReport(neue_standorte, neue_maschinen, neue_bohnen)


def formatiere(report: SeedReport) -> str:
    if (report.standorte, report.maschinen, report.kaffeebohnen) == (0, 0, 0):
        return "Keine Änderungen – alle Katalogdaten waren bereits vorhanden."
    return (
        f"Angelegt: {report.standorte} Standorte, {report.maschinen} Maschinen, "
        f"{report.kaffeebohnen} Kaffeebohnen."
    )


def main() -> None:
    database.create_schema()
    with database.session_factory() as session:
        print(formatiere(ergaenze_katalog(session, KATALOG)))
    database.dispose()


if __name__ == "__main__":
    main()

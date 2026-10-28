from podio import root_io

filename = "/eos/experiment/fcc/ee/simulation/key4hep_2026_10_02/91GeV/ALLEGRO_o2_v01/digi/output_ALLEGRO_DIGI_1_train.root"


reader = root_io.Reader(filename)
events = reader.get("events")
event = next(iter(events))

print("Collezioni disponibili nel primo evento:")
for name in event.getAvailableCollections():
    print(name)


def inspect_object(label, obj):
    print(f"\n--- {label} ---")
    print("Tipo:", type(obj))
    print("Metodi:", [
        name for name in dir(obj)
        if name.startswith("get")
        and not name.startswith("getObjectID")
    ])

straws = event.get("STTDigis")
links = event.get("STTSimDigiLinks")
simhits = event.get("STTCollection")

print("Numero straw digitizzate:", len(straws))
print("Numero link:", len(links))
print("Numero straw simulate:", len(simhits))

if len(straws):
    inspect_object("STTDigis[0]", straws[0])

if len(simhits):
    inspect_object("STTCollection[0]", simhits[0])

if len(links):
    link = links[0]
    inspect_object("STTSimDigiLinks[0]", link)

    for method in ("getFrom", "getTo"):
        if hasattr(link, method):
            try:
                obj = getattr(link, method)()
                inspect_object(method + "()", obj)
            except Exception as exc:
                print(method, "errore:", exc)

print("\n--- Metadati ---")
try:
    metadata = reader.get("metadata")[0]
    print("Tipo:", type(metadata))
    print("Metodi:", [
        name for name in dir(metadata)
        if "parameter" in name.lower()
    ])

    if hasattr(metadata, "get_parameter"):
        for key in (
            "STTCollection__CellIDEncoding",
            "STTDigis__CellIDEncoding",
            "DCHCollection__CellIDEncoding",
        ):
            try:
                print(key, "=", metadata.get_parameter(key))
            except Exception:
                pass
except Exception as exc:
    print("Lettura metadati non riuscita:", exc)

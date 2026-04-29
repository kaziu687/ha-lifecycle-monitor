# Lifecycle Monitor - Best Practices Fixes

- [x] 1. Zmienic `iot_class` w `manifest.json` z `"local_polling"` na `"calculated"`
- [x] 2. Dodac `MINOR_VERSION = 1` do config flow w `config_flow.py`
- [x] 3. Przeniesc wspolny kod (`_get_elapsed_days`, `suggested_object_id`, timer pattern) do `data.py` jako klase bazowa
- [x] 4. Dodac `EntityCategory.CONFIG` do button i datetime entities
- [x] 5. Zamienic sentinel `999999.0` na `None` z odpowiednia obsluga w sensorach i binary sensors
- [x] 6. Zmienic zapis czasu z lokalnego na UTC (`dt_util.utcnow()`)
- [x] 7. Usunac przestarzaly `async_register_entity_service` z `sensor.py`
- [x] 8. Ograniczyc target serwisow w `services.yaml`

# CT-400 error codes

- Document : MAN-CT-400-02
- Model : CT-400
- Type : manual
- Date : 2024-05-02

## Error code reference

| Code | Meaning | First action |
| --- | --- | --- |
| E-CT-110 | gantry over-temperature | check the gantry cooling fan ; replace it if airflow is below 80 percent |
| E-CT-220 | tube arcing detected | run the tube seasoning routine ; replace the tube assembly after three arcing events in 24 hours |
| E-CT-305 | slip ring communication loss | inspect and replace the slip ring brush kit |
| E-CT-410 | detector channel dropout | run detector calibration ; replace the module if dropout persists |

## General rule

Clear an error only after the cause is fixed. An error that returns within 24 hours
is escalated to second line with the full system log attached.

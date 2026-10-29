# Kazakhstan aviation fact-check and proposed focus-tree direction

**Scenario:** 1 January 2000 start, sandbox to approximately 2030.  
**Purpose:** separate confirmed procurement from proposals and unverified reporting. This note does not claim that all future scenarios are impossible; it marks what the reviewed public sources support.

## China
### Supported
- **Wing Loong I UAVs:** public research sources report Kazakhstan acquired Chinese Wing Loong I around 2016. This is a good historical anchor for a Chinese UAV focus, operator training and integration with ground forces.
- **Shaanxi Y-8F-200W/WA transports:** aircraft were acquired for Kazakhstan's National Guard, not automatically for the Air Force. Keep the service branch and transport role correct.
- Kazakhstan-China military cooperation, exercises, training and military-technical discussions are documented, but that alone does not prove a specific aircraft purchase.

### Not established by reviewed sources
No reliable confirmation was found that Kazakhstan received Chinese fighters such as J-7/J-10/J-11/J-35, or Chinese-supplied MiG-29s. Reports of interest, negotiations, images or speculation should not be turned into a confirmed historical delivery.

**Recommendation for `KAZ_buy_planes_from_china`:** rename to `KAZ_acquire_chinese_uav_systems` (“Освоение китайских беспилотных систем”), anchored on Wing Loong I. Use an appropriate UAV reward/tech bonus, operator training, Air XP or reconnaissance effect if the mod has such equipment. Do not give MiG-29 as a Chinese purchase. Inspect the actual event and ensure the reward is in executable effects, not only `effect_tooltip`. Since the game starts in 2000, the 2016 purchase belongs in a future focus/decision.

## United States
- **King Air B300ER Scorpion:** a possible sale of two ISR aircraft was approved by the US in 2020, but Kazakhstan had not received them according to statements in 2022; a 2025 report says Kazakhstan did not acquire the aircraft. Do not make them a historical delivered reward.
- **Puma UAV:** a public US contract record dated 11 September 2025 uses the title “UAS PUMA FOR KAZAKHSTAN” and lists around $4.5 million. This is a concrete lead, but the record alone does not establish the exact variant, quantity or delivery date. Verify primary contract/delivery details before assigning a number of units.
- **RQ-11 Raven:** some overviews mention US-origin small reconnaissance UAVs, but the exact quantity and supply details need stronger primary-source confirmation before scripting a precise reward.
- No confirmed Kazakh procurement of US F-16/F-15/F/A-18 fighters was found in the reviewed sources.

## Iran
No reliable confirmation was found in the reviewed public official sources that Kazakhstan purchased Iranian combat aircraft or strike UAVs. This is not proof that no confidential contacts existed, but it is insufficient to present such a purchase as historical fact.

**Recommendation for `KAZ_buying_tech_iran`:** remove it from the mandatory historical route or replace it with `KAZ_integrate_uav_forces` (“Интеграция беспилотных подразделений”). Do not duplicate Chinese and Israeli UAV roles with an unsupported Iran purchase. If an Iran-specific deal is desirable for sandbox gameplay, mark it as alternate history, make it optional and do not present it as a documented historical procurement.

## Israel and Turkey
- Israeli **Skylark** reconnaissance UAVs are reported in Kazakhstan's inventory.
- Kazakhstan contracted for three Turkish **ANKA** UAVs in 2021; public reporting describes testing and entry into service.
- A more credible tree should show diversified UAV sources and domestic integration/training rather than a mandatory purchase from Iran.

## Suggested aviation structure
1. **Reform the Air Defense Forces** — organization, pilot readiness, airbase support.
2. **Extend the life of the legacy fleet** — maintenance, spare parts, readiness of inherited aircraft.
3. **Develop multirole aviation** — Su-30SM training and maintenance; avoid oversized free aircraft rewards.
4. **Expand AHKE** — helicopter assembly/MRO, local components, technicians and crews; the enterprise already exists, so do not call this “creation”.
5. **Integrate army aviation** — troop transport, special forces support, evacuation and training.
6. **Integrate UAV units** — operators, reconnaissance, targeting and links to ground forces.
7. **Military transport aviation** — C-295/A400M maintenance and strategic mobility.
8. **Integrated air defense** — radar network, fighter/ground-based air defense coordination and counter-UAV.

## References
- RAND Chinese aviation export overview (includes Wing Loong export data): https://www.rand.org/content/dam/rand/pubs/research_reports/RR2500/RR2588/RAND_RR2588.pdf
- National Guard Y-8 reporting: https://polisia.kz/ru/park-aviatehniki-natsional-noj-gvardii-rk-popolnilsya-novym-samoletom/
- Informburo on National Guard Y-8F-200W: https://informburo.kz/stati/kak-lyotchiki-nacionalnoy-gvardii-osvaivayut-kitayskiy-voenno-transportnyy-samolyot-y8f-fotoreportazh.html
- Militarnyi on Y-8 deliveries: https://militarnyi.com/en/news/china-delivers-y-8f-aircraft-copies-of-soviet-an-12s-to-kazakhstan-s-national-guard/
- US contract record for Puma: https://www.federalcompass.com/fed-contract-award/W58RGZ25C0028
- Kazakhstan MOD on aircraft inventory: https://www.gov.kz/org/mod/press/news/details/604613?lang=ru
- Kazakhstan MOD on C-295: https://www.gov.kz/memleket/entities/mod/press/news/details/600880?lang=ru
- Kazakhstan MOD on A400M: https://www.gov.kz/memleket/entities/mod/press/news/details/921772?lang=ru
- Kazakhstan MOD on Su-30SM: https://www.gov.kz/org/mod/press/news/details/119230?lang=en
- Kazakhstan MOD on cooperation with China: https://www.gov.kz/memleket/entities/mod/press/news/details/362248?lang=ru

## Technical reminder
Before implementing any reward, inspect event files, equipment variants, technologies, localization and scripted effects. A model name in a tooltip is not evidence that the actual reward executes.

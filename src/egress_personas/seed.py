"""A starting set of tabs, written to data/ so the Sheet has something to be.

`personas init-data` writes these; upload them to Google Sheets as the eight tabs
and the team owns them from then on. Everything here is a starting point to be
argued with, and every row says how well supported it is: SOURCED means a citation
was read, ESTIMATE means it is reasoned from something adjacent, INVENTED means we
made it up because the model needs a number and nobody has measured one.

Where a citation was carried across from the project's existing evidence ledgers
rather than read first-hand for this registry, `read_by` is left blank and the note
says so. Filling those in is the literature review's first job.
"""

from __future__ import annotations

from pathlib import Path

ENUMS = """\
vocab,value,label,description,sort_order
phase,tts,Time to start,Affects pre-movement time,1
phase,tte,Time to exit,Affects travel time,2
phase,both,Both,Affects both phases,3
category,pre_evacuation,Pre-evacuation,"Waking, interpreting, deciding, gathering",1
category,wayfinding,Wayfinding,"Orientation, route and stair choice",2
category,social,Social,"Grouping, helping, warning, leading",3
category,fire_smoke,Fire and smoke,Response to the hazard itself,4
mechanism,set,Set,Replaces the value,1
mechanism,add,Add,Adds to the value,2
mechanism,mul,Multiply,Scales the value,3
mechanism,min,Floor,Raises the value to at least this,4
mechanism,max,Ceiling,Lowers the value to at most this,5
dist,const,Constant,p1 = value,1
dist,uniform,Uniform,"p1 = lo, p2 = hi",2
dist,normal,Normal,"p1 = mean, p2 = sd",3
dist,trunc_normal,Truncated normal,"p1 = mean, p2 = sd, p3 = lo, p4 = hi",4
dist,lognormal,Lognormal,"p1 = log mean, p2 = log sd",5
dist,weibull,Weibull,"p1 = scale, p2 = shape",6
dist,triangular,Triangular,"p1 = lo, p2 = mode, p3 = hi",7
dist,bernoulli,Bernoulli,p1 = probability,8
dist,categorical,Categorical,Uses the categories and weights columns,9
evidence,SOURCED,Sourced,A citation was read and supports this value,1
evidence,ESTIMATE,Estimate,Reasoned from an adjacent finding,2
evidence,INVENTED,Invented,No measurement exists; the model needs a number,3
effect_size,negligible,Negligible,,1
effect_size,small,Small,,2
effect_size,moderate,Moderate,,3
effect_size,large,Large,,4
effect_size,dominant,Dominant,Outweighs most other parameters,5
status,proposed,Proposed,Written down but not agreed,1
status,accepted,Accepted,Agreed and in use,2
status,parked,Parked,"Deliberately not used; the notes say why",3
status,rejected,Rejected,Considered and turned down,4
sex,female,Female,,1
sex,male,Male,,2
sex,other,Other,,3
mobility,none,No difficulty,Walks and uses stairs unaided,1
mobility,ambulatory_difficulty,Ambulatory difficulty,"Walks and uses stairs, but slower and tires sooner",2
mobility,walker_cane,Walker or cane,Uses an aid; stairs are slow and tiring,3
mobility,wheelchair,Wheelchair,Cannot use stairs; needs the lift or assistance,4
sim_agent_type,adult,Adult,,1
sim_agent_type,child,Child,Under 18,2
sim_agent_type,elderly,Elderly,65 and over,3
sim_agent_type,athletic,Athletic,,4
sim_agent_type,wheelchair,Wheelchair user,,5
sim_agent_type,visitor,Visitor,,6
sim_agent_type,caregiver,Caregiver,Paired with someone who cannot use stairs,7
household_role,head,Head,,1
household_role,partner,Partner,,2
household_role,child,Child,,3
household_role,parent,Parent,An older parent living with the household,4
household_role,lodger,Lodger,Shares the flat without being family,5
household_role,carer,Carer,Lives in to assist another member,6
household_role,other,Other,,7
age_band,0_17,Under 18,,1
age_band,18_34,18 to 34,,2
age_band,35_49,35 to 49,,3
age_band,50_64,50 to 64,,4
age_band,65_74,65 to 74,,5
age_band,75_plus,75 and over,,6
stair,north,North stair,,1
stair,south,South stair,,2
stair,none,No habit,Has no habitual stair,3
tie_kind,household,Household,Lives in the same flat,1
tie_kind,knock,Would knock,Would knock on their door on the way out,2
tie_kind,phone,Would phone,Would call or message them directly,3
tie_kind,group_chat,Building chat,Shares a building group chat,4
scope,same_floor,Same floor,Only between people on one floor,1
scope,adjacent_floor,Adjacent floor,One floor apart,2
scope,building,Building,Anywhere in the building,3
rate_kind,per_pair,Per pair,"The rate is the chance that any one eligible pair is tied",1
rate_kind,per_person_degree,Ties per person,"The rate is the average number of ties a person has, which does not change when the building gets bigger",2
time_of_day,day,Day,,1
time_of_day,night,Night,,2
alarm_quality,good,Good,Audible in every flat,1
alarm_quality,poor,Poor,"Corridor only; a quarter may not hear it",2
unit_letter,A,A,,1
unit_letter,B,B,,2
unit_letter,C,C,,3
unit_letter,D,D,,4
source_kind,paper,Paper,Peer-reviewed or conference paper,1
source_kind,dataset,Dataset,,2
source_kind,government,Government,Agency report or statistic,3
source_kind,code,Code,Building or fire code,4
source_kind,case,Case,Incident investigation,5
source_kind,procedure,Procedure,Fire service or operator procedure,6
source_kind,other,Other,,7
dimension,occupancy,Occupancy,People per flat,1
dimension,household_size,Household size,Share of households by size,2
dimension,age_band,Age,Share of residents by age band,3
dimension,sex,Sex,Share of residents by sex,4
dimension,mobility,Mobility,Share of residents by mobility category,5
dimension,absence,Absence,Share of residents not in the building,6
dimension,pet,Pet,Share of households keeping a pet,7
dimension,tenure,Tenure,Share of residents by years in the building,8
basis,acs,ACS,American Community Survey,1
basis,sipp,SIPP,Survey of Income and Program Participation,2
basis,paper,Paper,,3
basis,estimate,Estimate,,4
basis,team,Team,Agreed by the team without a source,5
basis,derived,Derived,Computed from another target,6
activity,asleep,Asleep,,1
activity,awake_home,Awake at home,,2
activity,cooking,Cooking,,3
activity,showering,Showering,Cannot hear the alarm and is not dressed,4
activity,out_of_flat,Out of the flat,In a corridor or lobby,5
"""

SOURCES = """\
id,short,cite,url,kind,year,finding,read_by,read_on,notes
proulx1995,Proulx 1995,"Proulx, G. (1995). Evacuation time and movement in apartment buildings. Fire Safety Journal 24(3), 229-246.",https://nrc-publications.canada.ca/eng/view/ft/?id=7b1d8203-c479-4e7a-b0ef-d43c7949c5d0,paper,1995,"Four apartment drills. Alarm audibility dominated time to start (169 s audible vs 515 s poor). 62% evacuated in groups, mostly pairs or threes, at the slowest member's pace. Residents chose familiar stairs over the nearest.",,,"Announced drills in 6-7 storey buildings, so a real fire is likely slower. Citation carried from the project's evidence ledger; not yet read first-hand for this registry."
proulx_fahy1997,Proulx and Fahy 1997,"Proulx, G. and Fahy, R. (1997). The time delay to start evacuation: review of five case studies. Fire Safety Science 5, 783-794.",https://publications.iafss.org/publications/fss/5/783/view/fss_5-783.pdf,paper,1997,"Residential time to start 169 s with a good alarm, 515 s with a poor one; pre-movement was about two thirds of total evacuation time. At Forest Laneway 24% did not hear the alarm.",,,"Citation carried from the project's evidence ledger; not yet read first-hand for this registry."
lovreglio2019,Lovreglio et al. 2019,"Lovreglio, R., Kuligowski, E., Gwynne, S. and Boyce, K. (2019). A pre-evacuation database for use in egress simulations. Fire Safety Journal 105, 107-128.",https://pure.ulster.ac.uk/ws/files/71289763/Lovreglio_et_al_Fire_Safety_Journal_January_2019.pdf,paper,2019,"Fitted residential pre-evacuation distributions: good-alarm cluster Weibull scale 102.475 s shape 0.767 (n=149); poor-alarm or real-fire cluster Weibull scale 724.617 s shape 0.978 (n=78).",,,"The lognormal rows of the same table are internally inconsistent between units; use the Weibull or gamma rows. Citation carried from the project's evidence ledger."
nist_ncstar_1_7,NIST NCSTAR 1-7,"Averill, J. et al. (2005). Occupant behavior, egress, and emergency communications. NIST NCSTAR 1-7, World Trade Center Investigation.",,case,2005,"About 70% of occupants milled - sought information or conferred - before evacuating. 30-34% helped others; 23-32% searched for others. Cues such as smoke made people leave slower, not faster, because they triggered sense-making first.",,,"An office population, so group and family effects transfer poorly to a residential tower. URL not yet recorded."
kuligowski_tn1632,Kuligowski NIST TN 1632,"Kuligowski, E. (2009). The process of human behavior in fires. NIST Technical Note 1632.",,government,2009,Sets out the perception-interpretation-decision-action model the TTS side of this project is built on.,,,URL not yet recorded.
sfpe_fruin,SFPE / Fruin,"SFPE Handbook of Fire Protection Engineering, movement chapters, following Fruin's pedestrian planning work.",,paper,,"Able-bodied adults walk about 1.19-1.25 m/s on the level; older adults are markedly slower; children are slower; assisted occupants much slower.",,,"Named in a comment on the team's first workbook. Edition, chapter and page still to be pinned down."
bohannon2008,Bohannon 2008,"Bohannon, R. (2008). Comfortable and maximum walking speed of adults aged 20-79 years: reference values and determinants.",,paper,2008,"Comfortable adult walking speed about 1.20 m/s with a standard deviation near 0.24 m/s.",,,"Citation carried from the project's evidence ledger; the standard deviation matters here because it is the spread this registry samples."
firetech2024_stairs,Fire Technology 2024,"Controlled stair-descent trials with older adults, Fire Technology (2024).",,paper,2024,Stair descent speeds for older adults are well below the able-bodied adult figures usually quoted.,,,"Named in a comment on the team's first workbook. Authors, title and volume still to be pinned down."
jin1978,Jin 1978,"Jin, T. (1978). Visibility through fire smoke.",,paper,1978,Walking speed falls as smoke reduces visibility; in irritant smoke people slow to about 0.3 m/s.,,,"Named in a comment on the team's first workbook."
fridolf2013,Fridolf et al. 2013,"Fridolf, K., Nilsson, D. and Frantzich, H. (2013). Movement speed and exit choice in smoke-filled rail tunnels.",,paper,2013,In dense smoke people slow to around 0.3 m/s and may crawl or follow a wall.,,,"Named in a comment on the team's first workbook."
frantzich_nilsson2003,Frantzich and Nilsson 2003,"Frantzich, H. and Nilsson, D. (2003). Utvardering av forsok med utrymning i rokfylld tunnel (Evacuation experiments in a smoke-filled tunnel).",,paper,2003,Speed-visibility relationships in smoke used for the smoke speed-reduction factors.,,,"Named in a comment on the team's first workbook."
acs_b11016,ACS B11016,"US Census Bureau, American Community Survey, table B11016 (household type by household size), San Francisco.",https://data.census.gov/table/ACSDT1Y2024.B11016,dataset,2024,"San Francisco households of 1 / 2 / 3 / 4-or-more people are 40.65 / 32.67 / 12.12 / 14.57 percent.",,,"Five-and-more folded into four. Flats in large buildings hold fewer people than the city average, which is why the occupancy target here is stated per flat and the size weights are tilted to match it."
acs_b18105,ACS B18105,"US Census Bureau, American Community Survey, table B18105 (ambulatory difficulty by age).",https://data.census.gov/table/ACSDT1Y2024.B18105,dataset,2024,"Ambulatory difficulty runs about 3.8 percent among adults aged 35-64 and about 18.2 percent among those 65 and over.",,,"This is the share the workbook's 'mobility impaired' category actually matches - not the much smaller wheelchair share."
sipp_wheelchair,SIPP wheelchair use,"US Census Bureau, Survey of Income and Program Participation, wheelchair and mobility device use.",,dataset,,About 1.3 percent of the adult population uses a wheelchair.,,,URL not yet recorded.
team_selfelicit_2026,Team self-elicitation 2026,"Fire on Floor 12 - what do I do? First-person walkthrough by the project team, three positions relative to the fire floor.",,other,2026,"Below the fire: alarm-only cue, assume a false alarm, check the hallway, the phone and the building group chat before leaving. On the fire floor: multi-sensory cues, alert the household, call 999/911 while moving, take the far stair. Above: cues delayed, contact people in the building, consider knocking on neighbours, shelter and seal if the stair is not clear.",project team,2026-09-22,"Recorded in context.md section 5. This is the only source for the building group chat as a warning channel, which is why those rows are INVENTED rather than ESTIMATE."
"""

PARAMETERS = """\
id,name,phase,category,target,applies_to,mechanism,dist,p1,p2,p3,p4,categories,weights,unit,lit_low,lit_high,effect_size,evidence,source_ids,finding,priority,sensitivity_rank,sensitivity_delta_tts_s,sensitivity_delta_tte_s,status,enabled,owner,last_reviewed,notes
P001,Walking speed - working-age adult,tte,wayfinding,body.base_speed,age_years >= 18 and age_years < 65 and mobility != wheelchair,set,trunc_normal,1.20,0.24,0.50,2.00,,,m/s,1.19,1.25,large,SOURCED,bohannon2008;sfpe_fruin,Comfortable adult walking speed about 1.20 m/s with sd near 0.24 m/s.,100,,,,accepted,TRUE,,,"The spread matters as much as the mean: it is what makes a crowd have a slow tail."
P002,Walking speed - 65 and over,tte,wayfinding,body.base_speed,age_years >= 65 and mobility != wheelchair,set,trunc_normal,0.95,0.22,0.40,1.60,,,m/s,0.90,1.00,large,ESTIMATE,sfpe_fruin;firetech2024_stairs,Older adults are markedly slower than able-bodied adults on the level and on stairs.,100,,,,proposed,TRUE,,,"The mean is reasoned from the simulation's sourced elderly range rather than read off a table. Needs the Fire Technology 2024 trial pinned down."
P003,Walking speed - under 18,tte,wayfinding,body.base_speed,age_years < 18 and mobility != wheelchair,set,trunc_normal,0.95,0.20,0.40,1.50,,,m/s,0.73,1.20,moderate,ESTIMATE,sfpe_fruin;proulx1995,Children are slower than adults; small children occupied the full stair width and were not carried.,100,,,,proposed,TRUE,,,"Proulx measured 0.33 m/s on stairs for 2-5 year olds, which is a stair figure, not this level figure."
P004,Walking speed - wheelchair,tte,wayfinding,body.base_speed,mobility == wheelchair,set,trunc_normal,0.68,0.20,0.30,1.10,,,m/s,0.30,1.06,moderate,ESTIMATE,sfpe_fruin,Assisted and wheeled occupants are much slower than able-bodied adults.,110,,,,proposed,TRUE,,,"Range reasoned from the simulation's sourced wheelchair profile. These occupants cannot use stairs at all, which matters far more than their level speed."
P005,Walking speed - ambulatory difficulty,tte,wayfinding,body.base_speed,mobility in [ambulatory_difficulty walker_cane],mul,const,0.66,,,,,,factor,,,moderate,SOURCED,acs_b18105,Occupants who walk with difficulty move at about two thirds of the able-bodied speed.,120,,,,accepted,TRUE,,,"Applied on top of the age-based speed, so an older person with a cane gets both effects."
P006,Carrying or handling a pet,tte,pre_evacuation,body.base_speed,has_pet == TRUE,mul,const,0.90,,,,,,factor,,,small,ESTIMATE,,A pet occupies a hand and slows both level and stair movement by about a tenth.,130,,,,proposed,TRUE,,,"Carried over as a claim from the team's first workbook (rule S103). No source was attached to it there and none has been found since."
P007,Patience behind a blockage,tte,wayfinding,body.patience_s,,set,uniform,40,80,,,,,s,60,300,moderate,INVENTED,,How long somebody stands in a stalled queue before giving up on that staircase.,100,,,,parked,TRUE,,,"The simulation uses 40-80 s and flags it as invented. Queue tolerance measured in lift queues runs 1-5 minutes, so this is probably too impatient. Worth an early sensitivity run."
P008,Tries the other staircase after turning back,tte,wayfinding,body.tries_other_stair,,set,bernoulli,0.23,,,,,,share,,,small,SOURCED,,"Of those who turn back from smoke, about a quarter try the other staircase rather than going home.",100,,,,accepted,TRUE,,,"Matches the simulation's sourced other_stair_share. The source behind that value still needs recording here."
P010,Milling - baseline,tts,pre_evacuation,dispositions.mill_tendency,,set,trunc_normal,0.70,0.18,0.00,1.00,,,share,0.60,0.80,dominant,SOURCED,nist_ncstar_1_7,About 70 percent of WTC occupants milled - sought information or conferred - before evacuating.,100,,,,accepted,TRUE,,,"NIST's figure is for an office population. A residential tower at night may differ, and that difference is one of the things this project is for."
P011,Milling - a new tenant has fewer people to confer with,tts,social,dispositions.mill_tendency,tenure_years <= 1,mul,const,0.65,,,,,,factor,,,moderate,ESTIMATE,proulx1995,"Milling is information-seeking from other people; somebody who knows nobody in the building has fewer to seek it from.",110,,,,proposed,TRUE,,,"Reasoned, not measured. Proulx supports that residents rely on familiar people and routes, not this size of effect."
P012,Milling - living alone,tts,social,dispositions.mill_tendency,lives_alone == TRUE,mul,const,0.85,,,,,,factor,,,small,ESTIMATE,proulx1995,Conferring with a household member is the commonest first response; somebody alone skips it.,110,,,,proposed,TRUE,,,Reasoned from Proulx's finding that 62 percent left in groups.
P020,Seeks a second cue before moving,tts,pre_evacuation,dispositions.seeks_confirmation,,set,trunc_normal,0.55,0.20,0.00,1.00,,,share,,,large,ESTIMATE,nist_ncstar_1_7;team_selfelicit_2026,"Looking for confirmation - the hallway, a neighbour, a siren, the news - before accepting that an alarm is real.",100,,,,proposed,TRUE,,,"NIST lists looking for confirmation as a behaviour pattern but gives no per-person propensity, so the distribution is ours."
P021,Seeks a second cue - poor alarm,tts,pre_evacuation,dispositions.seeks_confirmation,alarm_quality == poor,add,const,0.15,,,,,,share,,,moderate,ESTIMATE,proulx1995;proulx_fahy1997,A corridor-only alarm is ambiguous where an in-flat alarm is not.,110,,,,proposed,TRUE,,,"The alarm effect on time to start is well measured; routing it through this disposition rather than straight into a delay is our modelling choice."
P022,Compliance with instructions,tts,pre_evacuation,dispositions.authority_compliance,,set,trunc_normal,0.60,0.20,0.00,1.00,,,share,,,large,ESTIMATE,kuligowski_tn1632,Willingness to act on an alarm or an announcement rather than reinterpret it.,100,,,,proposed,TRUE,,,"In the real residential cases nearly every later instruction came from firefighters in person, which this does not yet capture."
P023,Altruism,tts,social,dispositions.altruism,,set,trunc_normal,0.32,0.18,0.00,1.00,,,share,0.30,0.34,moderate,SOURCED,nist_ncstar_1_7,"30 to 34 percent of WTC occupants helped others; 23 to 32 percent searched for others.",100,,,,accepted,TRUE,,,"An office population with no family present still spent this much effort on others, so a residential figure is likely higher."
P024,Leadership,tts,social,dispositions.leadership,,set,trunc_normal,0.30,0.18,0.00,1.00,,,share,,,moderate,INVENTED,,Tendency to direct others rather than follow.,100,,,,proposed,TRUE,,,"No measurement found. Named as a factor in the project's reading but never quantified."
P025,Leadership - head of household,tts,social,dispositions.leadership,household_role == head,add,const,0.15,,,,,,share,,,small,ESTIMATE,proulx1995,One member typically decides for the household and the rest follow.,110,,,,proposed,TRUE,,,Reasoned from households deciding together.
P026,Risk tolerance,tte,fire_smoke,dispositions.risk_tolerance,,set,trunc_normal,0.40,0.18,0.00,1.00,,,share,,,moderate,INVENTED,,Willingness to enter a route they can see is degraded.,100,,,,proposed,TRUE,,,"Drives the smoke turn-back decision, which the simulation currently draws from a population share rather than a disposition."
P027,Risk tolerance - 65 and over,tte,fire_smoke,dispositions.risk_tolerance,age_years >= 65,mul,const,0.80,,,,,,factor,,,small,INVENTED,,Older occupants were more likely to shelter than to attempt a degraded route.,110,,,,proposed,TRUE,,,"A guess consistent with the Forest Laneway pattern, where most early evacuation attempts failed and residents sheltered."
P030,Knows the building - new tenant,tte,wayfinding,knowledge.floorplan_familiarity,tenure_years < 1,set,trunc_normal,0.35,0.15,0.00,1.00,,,share,,,moderate,ESTIMATE,proulx1995,Residents chose familiar stairs over the nearest ones.,100,,,,proposed,TRUE,,,"Proulx supports the mechanism; the three tenure bands and their means are ours."
P031,Knows the building - one to five years,tte,wayfinding,knowledge.floorplan_familiarity,tenure_years >= 1 and tenure_years < 5,set,trunc_normal,0.65,0.15,0.00,1.00,,,share,,,moderate,ESTIMATE,proulx1995,As above.,100,,,,proposed,TRUE,,,
P032,Knows the building - five years or more,tte,wayfinding,knowledge.floorplan_familiarity,tenure_years >= 5,set,trunc_normal,0.85,0.12,0.00,1.00,,,share,,,moderate,ESTIMATE,proulx1995,As above.,100,,,,proposed,TRUE,,,
P033,Knows a second staircase exists - new tenant,tte,wayfinding,knowledge.knows_second_stair,tenure_years < 1,set,bernoulli,0.45,,,,,,share,,,large,INVENTED,,Whether they know there is another way down at all.,100,,,,proposed,TRUE,,,"Nobody has measured this and it may matter a great deal, because not knowing removes the alternative the model relies on."
P034,Knows a second staircase exists - established resident,tte,wayfinding,knowledge.knows_second_stair,tenure_years >= 1,set,bernoulli,0.85,,,,,,share,,,large,INVENTED,,As above.,100,,,,proposed,TRUE,,,
P035,Habitual staircase,tte,wayfinding,knowledge.habitual_stair,,set,categorical,,,,,north;south,1;1,,,,moderate,ESTIMATE,proulx1995,"Residents chose familiar stairs over the nearest, so each has a habit to reach for.",100,,,,proposed,TRUE,,,"Split evenly for want of anything better. In a real building the split follows which stair is nearer each flat."
P036,False alarms lived through - one to five years,tts,pre_evacuation,knowledge.prior_false_alarms,tenure_years >= 1 and tenure_years < 5,set,uniform,0,3,,,,,count,,,moderate,INVENTED,,How many times the bell has already cried wolf here.,100,,,,proposed,TRUE,,,"Both effects are documented for the 1993 WTC bombing - experience made some faster and some slower - and nothing here yet uses this field."
P037,False alarms lived through - five years or more,tts,pre_evacuation,knowledge.prior_false_alarms,tenure_years >= 5,set,uniform,1,8,,,,,count,,,moderate,INVENTED,,As above.,100,,,,proposed,TRUE,,,
P038,Fire safety training,tts,pre_evacuation,knowledge.fire_safety_training,,set,bernoulli,0.10,,,,,,share,,,small,INVENTED,,Any drill or training in this building.,100,,,,proposed,TRUE,,,Residential towers rarely drill; a tenth is a guess.
P040,Hears the alarm - good alarm,tts,pre_evacuation,situation.alarm_audible,alarm_quality == good,set,bernoulli,0.98,,,,,,share,0.95,1.00,dominant,SOURCED,proulx1995,In the buildings with an alarm inside each flat every occupant heard it.,100,,,,accepted,TRUE,,,"Audibility was the single largest driver of time to start: 169 s audible against 515 s poor."
P041,Hears the alarm - poor alarm,tts,pre_evacuation,situation.alarm_audible,alarm_quality == poor,set,bernoulli,0.76,,,,,,share,0.75,0.77,dominant,SOURCED,proulx1995;proulx_fahy1997,"Between 23 and 25 percent of residents did not hear a corridor-only alarm from inside the flat; 24 percent at Forest Laneway.",100,,,,accepted,TRUE,,,
P090,Pre-movement time,tts,pre_evacuation,body.delay_s,,set,weibull,102.475,0.767,,,,,s,,,dominant,SOURCED,lovreglio2019,"Good-alarm residential cluster: Weibull scale 102.475 s, shape 0.767, n = 149. Implied mean 120 s.",100,,,,parked,FALSE,,,"PARKED ON PURPOSE, and switched off. The simulation already fits this from the same source, per scenario and by time of day, and the two clusters differ by a factor of six. Setting it here would freeze one cluster into every run. Left in the registry because the value is the right one to argue about, and because it records why we do not emit it."
"""

POPULATION = """\
id,dimension,category,value,unit,tolerance,basis,source_ids,notes
T001,occupancy,persons_per_flat,1.66,persons,0.15,estimate,acs_b11016,"Flats in large San Francisco buildings hold fewer people than the city average of 2.14. This is the primary occupancy target because it is plan-independent: a per-floor figure only means something once you fix how many flats a floor has."
T010,household_size,1,40.65,share,,acs,acs_b11016,San Francisco households of one person.
T011,household_size,2,32.67,share,,acs,acs_b11016,Two people.
T012,household_size,3,12.12,share,,acs,acs_b11016,Three people.
T013,household_size,4plus,14.57,share,,acs,acs_b11016,"Four or more, folded to exactly four."
T020,age_band,0_17,0.12,share,0.04,estimate,,"Reasoned to fit a tower of mostly small flats. Needs a real San Francisco figure."
T021,age_band,18_34,0.27,share,0.04,acs,,Ages 18 to 34 at 27 percent.
T022,age_band,35_49,0.24,share,0.04,estimate,,Needs a real figure.
T023,age_band,50_64,0.19,share,0.04,estimate,,Needs a real figure.
T024,age_band,65_74,0.11,share,0.03,estimate,,Needs a real figure.
T025,age_band,75_plus,0.07,share,0.03,estimate,,"Needs a real figure. This band and the one above it drive the stair-speed tail, so they are worth getting right early."
T030,sex,female,0.50,share,0.04,estimate,,
T031,sex,male,0.50,share,0.04,estimate,,
T040,mobility,wheelchair,0.013,share,0.008,sipp,sipp_wheelchair,"About 1.3 percent use a wheelchair. These are the occupants who cannot use the stairs at all, so the count matters more than the share."
T041,mobility,ambulatory_difficulty@18_64,0.038,share,0.015,acs,acs_b18105,Ambulatory difficulty among adults aged 35 to 64.
T042,mobility,ambulatory_difficulty@65_plus,0.182,share,0.04,acs,acs_b18105,"Ambulatory difficulty among those 65 and over. This, not the wheelchair share, is what the team's first workbook's 'mobility impaired' category was actually describing."
T050,absence,share,0.06,share,0.03,estimate,,"Residents not in the building. Overridden per scenario: a weekday afternoon empties a tower that a 3 a.m. fire does not."
T060,pet,share,0.25,share,0.10,estimate,,"Share of flats keeping a pet. The team's first workbook had 11 of 92 flats, about 12 percent; US household figures are far higher. Neither is a San Francisco apartment figure."
T070,tenure,lt_1,0.18,share,0.06,estimate,,"Residents in their first year. Drives how much of the building they know."
T071,tenure,1_5,0.37,share,0.08,estimate,,
T072,tenure,5_plus,0.45,share,0.08,estimate,,"Needs a real figure: San Francisco rent control makes long tenures commoner here than nationally, which would raise familiarity across the board."
"""

SOCIAL = """\
id,tie_kind,scope,rate_kind,tenure_ref_years,min_age_years,formation_rate,strength_dist,s1,s2,s3,s4,symmetric,evidence,source_ids,finding,notes
S001,household,building,per_pair,,,1.00,const,1.00,,,,TRUE,SOURCED,proulx1995,"62 percent of residents evacuated in groups, mostly pairs or threes, moving at the slowest member's pace.",Structural rather than drawn: everyone in a flat is tied to everyone else in it. The rate is here for the record.
S010,knock,same_floor,per_pair,3,18,0.35,uniform,0.30,0.90,,,TRUE,ESTIMATE,proulx1995;nist_ncstar_1_7,"30 to 34 percent of WTC occupants helped others; Proulx's seniors gathered on the landing before leaving together.","The chance that two people on one floor know each other well enough that one would knock on the way out. Reasoned from helping rates rather than measured. tenure_ref_years = 3 means somebody three years in is as connected as an established resident and a new tenant is much less so, which is how a persona ends up genuinely knowing nobody."
S011,knock,adjacent_floor,per_pair,4,18,0.06,uniform,0.20,0.60,,,TRUE,INVENTED,,,"Knowing a neighbour a floor away is commoner than knowing a stranger twelve floors up and rarer than knowing the person opposite. The number is a guess."
S020,phone,building,per_person_degree,3,18,0.60,uniform,0.50,1.00,,,TRUE,ESTIMATE,nist_ncstar_1_7,Calling loved ones is one of NIST's listed pre-evacuation behaviours.,"A tie you would use the phone for, anywhere in the building. Stated as an average number of such ties per person rather than a chance per pair: a per-pair rate would silently mean six phone contacts in a 27-floor tower and one in a 5-floor block, so it could not be carried from one building to another."
S030,group_chat,building,per_person_degree,1,18,0.45,uniform,0.10,0.50,,,FALSE,INVENTED,team_selfelicit_2026,"The team's own first-person walkthrough checks the building group chat before leaving.",A per-person membership draw against one chat node rather than a tie to each other member - otherwise the graph would be dense and say nothing. No measurement exists for this channel at all.
"""

SCENARIOS = """\
scenario_id,plan_id,building_json,num_floors,time_of_day,alarm_quality,fire_floor_label,absent_share,asleep_share,out_of_flat_share,default_seed,notes
night_fire12,plan2_drawing_v2_2,buildings/plan2_drawing_v2_2.json,27,night,good,12,0.04,0.95,0.00,1234,"The reference case: 3 a.m., almost everyone home and asleep, alarm audible in every flat, fire starting on floor 12."
night_poor_alarm,plan2_drawing_v2_2,buildings/plan2_drawing_v2_2.json,27,night,poor,12,0.04,0.95,0.00,1234,"The same night with a corridor-only alarm, which is the condition Proulx measured at 515 s rather than 169 s. The comparison against night_fire12 isolates audibility."
day_fire12,plan2_drawing_v2_2,buildings/plan2_drawing_v2_2.json,27,day,good,12,0.28,0.02,0.01,1234,"A weekday afternoon: a quarter of residents are out, nobody is asleep, and the people at home skew older and less mobile."
"""

CASE_COLUMNS = (
    "case_id", "name", "unit", "household_id", "household_role", "age_years", "sex",
    "mobility", "tenure_years", "present", "asleep", "activity", "alarm_audible",
    "has_pet", "floorplan_familiarity", "habitual_stair", "knows_second_stair",
    "prior_false_alarms", "fire_safety_training", "mill_tendency",
    "seeks_confirmation", "authority_compliance", "altruism", "risk_tolerance",
    "leadership", "commitments", "narrative_override", "notes",
)

#: The hand-authored cases. Written as records rather than CSV text because this is
#: the widest tab, and a single missing comma in a hand-aligned row shifts every value
#: after it one column left - which parses cleanly and means something else entirely.
#: Any key left out is sampled like anybody else's, which is what makes a case a
#: partial pin rather than a full specification.
CASE_ROWS: tuple[dict[str, object], ...] = (
    {
        "case_id": "C01", "name": "Long-tenured widow above the fire", "unit": "18C",
        "household_id": "HH-18C", "household_role": "head", "age_years": 79,
        "sex": "female", "mobility": "walker_cane", "tenure_years": 31,
        "present": True, "asleep": True, "activity": "asleep", "has_pet": False,
        "floorplan_familiarity": 0.95, "habitual_stair": "south",
        "knows_second_stair": True, "prior_false_alarms": 11,
        "fire_safety_training": False, "seeks_confirmation": 0.70,
        "authority_compliance": 0.80, "risk_tolerance": 0.20,
        "notes": "Eleven false alarms in thirty-one years, a walker, and nine floors "
                 "of stairs between her and the street. Tests the case where knowing "
                 "the building perfectly does not help.",
    },
    {
        "case_id": "C02", "name": "New tenant below the fire", "unit": "6B",
        "household_id": "HH-06B", "household_role": "head", "age_years": 24,
        "sex": "male", "mobility": "none", "tenure_years": 0.2,
        "present": True, "asleep": True, "activity": "asleep", "has_pet": False,
        "floorplan_familiarity": 0.20, "knows_second_stair": False,
        "prior_false_alarms": 0, "fire_safety_training": False,
        "mill_tendency": 0.30, "altruism": 0.15, "risk_tolerance": 0.70,
        "leadership": 0.10,
        "notes": "Moved in three weeks ago, knows nobody, and has never noticed the "
                 "second staircase. The opposite of C01: mobile and quick, but blind.",
    },
    {
        "case_id": "C03", "name": "Mother of a small child, with a cat", "unit": "14A",
        "household_id": "HH-14A", "household_role": "head", "age_years": 38,
        "sex": "female", "mobility": "none", "tenure_years": 6,
        "present": True, "asleep": True, "activity": "asleep", "has_pet": True,
        "floorplan_familiarity": 0.85, "habitual_stair": "north",
        "knows_second_stair": True, "fire_safety_training": False,
        "altruism": 0.70, "leadership": 0.75,
        "commitments": "pet:the cat:60;child:the toddler:120",
        "notes": "Two floors above the fire with a toddler to carry and a cat that "
                 "hides. Gathering time, not walking speed, decides this "
                 "household's outcome.",
    },
    {
        "case_id": "C04", "name": "Her partner", "unit": "14A",
        "household_id": "HH-14A", "household_role": "partner", "age_years": 41,
        "sex": "male", "mobility": "none", "tenure_years": 6,
        "present": True, "asleep": True, "activity": "asleep", "has_pet": True,
        "floorplan_familiarity": 0.80, "habitual_stair": "north",
        "knows_second_stair": True, "fire_safety_training": False,
        "altruism": 0.60, "leadership": 0.40,
        "notes": "The second adult in C03's flat. Whether the household waits for "
                 "each other is the thing to watch.",
    },
    {
        "case_id": "C05", "name": "Their toddler", "unit": "14A",
        "household_id": "HH-14A", "household_role": "child", "age_years": 3,
        "sex": "female", "mobility": "none", "tenure_years": 3,
        "present": True, "asleep": True, "activity": "asleep", "has_pet": True,
        "floorplan_familiarity": 0.05, "habitual_stair": "none",
        "knows_second_stair": False, "prior_false_alarms": 0,
        "fire_safety_training": False, "leadership": 0.0,
        "notes": "Three years old. Cannot evacuate alone under any circumstances, "
                 "and sets the household's pace.",
    },
    {
        "case_id": "C06", "name": "Wheelchair user living alone", "unit": "21D",
        "household_id": "HH-21D", "household_role": "head", "age_years": 56,
        "sex": "male", "mobility": "wheelchair", "tenure_years": 9,
        "present": True, "asleep": True, "activity": "asleep", "has_pet": False,
        "floorplan_familiarity": 0.90, "habitual_stair": "none",
        "knows_second_stair": True, "fire_safety_training": True,
        "mill_tendency": 0.20, "seeks_confirmation": 0.30,
        "authority_compliance": 0.85, "altruism": 0.30, "risk_tolerance": 0.20,
        "leadership": 0.40,
        "notes": "Cannot use the stairs and has nobody in the flat to help. The "
                 "simulation looks for a caregiver on the same floor and will not "
                 "find one, so this persona is the deliberate test of that gap.",
    },
    {
        "case_id": "C07", "name": "Resident on the fire floor", "unit": "12B",
        "household_id": "HH-12B", "household_role": "head", "age_years": 45,
        "sex": "male", "mobility": "none", "tenure_years": 13,
        "present": True, "asleep": True, "activity": "asleep", "has_pet": False,
        "floorplan_familiarity": 0.90, "habitual_stair": "north",
        "knows_second_stair": True, "prior_false_alarms": 4,
        "fire_safety_training": False, "mill_tendency": 0.10,
        "seeks_confirmation": 0.10, "authority_compliance": 0.50, "altruism": 0.85,
        "risk_tolerance": 0.70, "leadership": 0.85,
        "notes": "Smoke and noise reach him before the alarm does, so his cues are "
                 "unambiguous. High altruism and high leadership: the neighbour who "
                 "knocks on doors.",
    },
    {
        "case_id": "C08", "name": "Night-shift nurse, awake and dressed", "unit": "9A",
        "household_id": "HH-09A", "household_role": "head", "age_years": 33,
        "sex": "female", "mobility": "none", "tenure_years": 2,
        "present": True, "asleep": False, "activity": "awake_home", "has_pet": False,
        "floorplan_familiarity": 0.60, "habitual_stair": "south",
        "knows_second_stair": True, "prior_false_alarms": 1,
        "fire_safety_training": True, "mill_tendency": 0.15,
        "seeks_confirmation": 0.20, "authority_compliance": 0.90, "altruism": 0.80,
        "risk_tolerance": 0.50, "leadership": 0.70,
        "notes": "Awake, dressed and trained when the alarm goes. The fastest "
                 "realistic responder in the building, and a plausible informal "
                 "leader on her floor.",
    },
)


def _cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return str(v)


def cases_csv() -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CASE_COLUMNS)
    for row in CASE_ROWS:
        unknown = set(row) - set(CASE_COLUMNS)
        assert not unknown, f"{row['case_id']}: unknown key(s) {unknown}"
        w.writerow([_cell(row.get(c)) for c in CASE_COLUMNS])
    return buf.getvalue()


def building_csv(plan_id: str = "plan2_drawing_v2_2") -> str:
    """Floors 4 to 27 with no 13, four flats a floor, and one seed tile per letter.

    `sim_floor` keeps the building's own numbering minus the missing 13, so floor 27
    is the simulation's floor 26 and floors 1 to 3 stay unoccupied - which is what
    the team's first workbook asserted too. The seed tiles are the A/B/C/D positions
    from the project's own floorplan inspector; they are estimates read off a
    drawing, not a verified flat index, and `personas report` says so.
    """
    seeds = {"A": (30, 16), "B": (22, 2), "C": (2, 15), "D": (2, 2)}
    note = {
        "A": '"Seed tile read off the team\'s plan 2 drawing: an estimate, '
             'not a verified flat index."',
        "B": "", "C": "", "D": "",
    }
    lines = ["unit_label,floor_label,unit_letter,sim_floor,plan_id,"
             "seed_tile_x,seed_tile_y,occupiable,notes"]
    for floor in range(4, 28):
        if floor == 13:
            continue
        sim_floor = floor - 1 if floor > 13 else floor
        for letter in "ABCD":
            x, y = seeds[letter]
            lines.append(
                f"{floor}{letter},{floor},{letter},{sim_floor},{plan_id},"
                f"{x},{y},TRUE,{note[letter]}"
            )
    return "\n".join(lines) + "\n"


FILES: dict[str, str] = {
    "enums.csv": ENUMS,
    "sources.csv": SOURCES,
    "parameters.csv": PARAMETERS,
    "population.csv": POPULATION,
    "social.csv": SOCIAL,
    "scenarios.csv": SCENARIOS,
}


def write(dest: Path, force: bool = False) -> list[Path]:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    generated = [("building.csv", building_csv()), ("cases.csv", cases_csv())]
    for name, body in list(FILES.items()) + generated:
        path = dest / name
        if path.exists() and not force:
            continue
        path.write_text(body, encoding="utf-8")
        written.append(path)
    return written

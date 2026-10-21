# What this building is made of

**the base building** · night_fire12 · seed 1234

151 residents in 92 households across 92 flats.

## Distributions

**Age** — mean 43.06, median 41.00, 5th–95th 11.00–74.50 years

```
  0–18      14   9.3%  ############
  18–25     19  12.6%  ################
  25–35     23  15.2%  ####################
  35–50     40  26.5%  ##################################
  50–65     28  18.5%  ########################
  65–75     19  12.6%  ################
  75–101     8   5.3%  #######
```

**Age band**

```
  0_17       14   9.3%  ###########
  18_34      42  27.8%  ##################################
  35_49      40  26.5%  ################################
  50_64      28  18.5%  #######################
  65_74      19  12.6%  ###############
  75_plus     8   5.3%  ######
```

**Sex**

```
  female    77  51.0%  ##################################
  male      74  49.0%  #################################
  other      0   0.0%  
```

**Mobility**

```
  none                    140  92.7%  ##################################
  ambulatory_difficulty     4   2.6%  #
  walker_cane               6   4.0%  #
  wheelchair                1   0.7%  
```

**Occupant class**

```
  adult        109  72.2%  ##################################
  child         14   9.3%  ####
  elderly       27  17.9%  ########
  wheelchair     1   0.7%  
  caregiver      0   0.0%  
  athletic       0   0.0%  
  visitor        0   0.0%  
```

**Household size**

```
  1    50  54.3%  ##################################
  2    31  33.7%  #####################
  3     5   5.4%  ###
  4     6   6.5%  ####
  5     0   0.0%  
```

**Role in the flat**

```
  head       92  60.9%  ##################################
  partner    26  17.2%  ##########
  child      14   9.3%  #####
  parent     10   6.6%  ####
  carer       0   0.0%  
  lodger      9   6.0%  ###
  other       0   0.0%  
```

**Years in the building** — mean 7.58, median 4.60, 5th–95th 0.40–26.40 years

```
  0–1      22  14.6%  #####################
  1–2      22  14.6%  #####################
  2–5      36  23.8%  ##################################
  5–10     30  19.9%  ############################
  10–20    22  14.6%  #####################
  20–31    19  12.6%  ##################
```

**Walking speed** — mean 1.06, median 1.05, 5th–95th 0.62–1.46 m/s

```
  0.2–0.6     7   4.6%  ######
  0.6–0.8    20  13.2%  ##################
  0.8–1      36  23.8%  ################################
  1–1.2      37  24.5%  #################################
  1.2–1.4    38  25.2%  ##################################
  1.4–1.6    10   6.6%  #########
  1.6–2       3   2.0%  ###
```

**Knows the layout** — mean 0.68, median 0.71, 5th–95th 0.30–0.95 0–1

```
  0–0.2       5   3.3%  ###
  0.2–0.4    11   7.3%  #######
  0.4–0.6    28  18.5%  ##################
  0.6–0.8    54  35.8%  ##################################
  0.8–1      53  35.1%  #################################
```

**Confers before acting** — mean 0.59, median 0.58, 5th–95th 0.29–0.88 0–1

```
  0–0.2       3   2.0%  ##
  0.2–0.4    20  13.2%  ############
  0.4–0.6    56  37.1%  ##################################
  0.6–0.8    53  35.1%  ################################
  0.8–1      19  12.6%  ############
```

**Connections each** — mean 4.14, median 4.00, 5th–95th 1.00–8.00 ties

```
  0–1      5   3.3%  ####
  1–2     17  11.3%  #############
  2–4     43  28.5%  ##################################
  4–6     43  28.5%  ##################################
  6–9     38  25.2%  ##############################
  9–15     5   3.3%  ####
```

**What they are doing**

```
  asleep       135  95.1%  ##################################
  awake_home     7   4.9%  ##
```

## Crosstabs

A marginal share can be right while the joint distribution is wrong: the building can hold the right number of over-65s and the wrong number of them living alone.

**age / mobility**

Mobility is drawn conditioned on age, so this table is where that shows.

| age | none | ambulatory_difficulty | walker_cane | wheelchair | all |
|---|---|---|---|---|---|
| 0_17 | 14 | · | · | · | 14 |
| 18_34 | 40 | 1 | 1 | · | 42 |
| 35_49 | 39 | · | 1 | · | 40 |
| 50_64 | 25 | · | 2 | 1 | 28 |
| 65_74 | 17 | 2 | · | · | 19 |
| 75_plus | 5 | 1 | 2 | · | 8 |
| **all** | 140 | 4 | 6 | 1 | 151 |

**age / sex**

| age | female | male | all |
|---|---|---|---|
| 0_17 | 7 | 7 | 14 |
| 18_34 | 24 | 18 | 42 |
| 35_49 | 17 | 23 | 40 |
| 50_64 | 15 | 13 | 28 |
| 65_74 | 10 | 9 | 19 |
| 75_plus | 4 | 4 | 8 |
| **all** | 77 | 74 | 151 |

**age / household**

Somebody living alone has nobody in the flat to wake them or wait for them.

| age | alone | with others | all |
|---|---|---|---|
| 0_17 | · | 14 | 14 |
| 18_34 | 17 | 25 | 42 |
| 35_49 | 15 | 25 | 40 |
| 50_64 | 10 | 18 | 28 |
| 65_74 | 5 | 14 | 19 |
| 75_plus | 3 | 5 | 8 |
| **all** | 50 | 101 | 151 |

**mobility / help**

Of those who do not walk freely, who has somebody in the flat. The last column is the gap the simulation cannot close either.

| mobility | others in the flat | alone in the flat | all |
|---|---|---|---|
| ambulatory_difficulty | 4 | · | 4 |
| walker_cane | 2 | 4 | 6 |
| wheelchair | · | 1 | 1 |
| **all** | 6 | 5 | 11 |

## What this does to an evacuation

Inputs to RSET, not RSET. Nothing here simulates anything; these are the quantities the simulation reads, grouped by which half of the split they land on.

| | driver | value | why it matters |
|---|---|---|---|
| — | in the building | **142** people | Everything below is of these. |
| TTS | asleep when it starts | **95%** share | Waking is the first and largest part of pre-movement. |
| TTS | cannot hear the alarm | **3** people | Audibility was the largest single driver Proulx measured: 169 s against 515 s. |
| TTS | nobody would warn them | **5** people | No household, no neighbour, no phone, not in the chat. For these the alarm is the only cue there is. |
| TTS | confers before acting, mean | **0.59** 0–1 | NIST found about 70% of occupants milled before evacuating. |
| TTS | seeks a second cue, mean | **0.54** 0–1 | A corridor-only alarm raises this; an in-flat one does not. |
| TTS | will not leave without something | **36** people | A pet, a child, documents. Time spent before the door, not after it. |
| TTS | gathering, per resident | **12** seconds | Averaged over everybody in the building, so it can be compared between buildings of different size. Time spent before the door, not after it. |
| TTE | walking speed, mean | **1.06** m/s | On the level and uncrowded; the simulation slows this for density, smoke and stairs. |
| TTE | walking speed, slowest twentieth | **0.64** m/s | A household moves at its slowest member's pace, so the tail matters more than the mean. |
| TTE | walks with difficulty | **9** people | Uses the stairs, but slower and tires sooner. |
| TTE | cannot use the stairs at all | **1** people | Depends on the lift or on being carried. |
| TTE | of those, nobody in the flat to help | **1** people | The simulation looks for a caregiver on the same floor and will not find one for a one-person household. |
| TTE | does not know a second staircase exists | **32** people | Removes the alternative the model relies on when one stair blocks. |
| TTE | knows the layout, mean | **0.68** 0–1 | Residents chose familiar stairs over nearer ones (Proulx 1995). |

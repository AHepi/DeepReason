# Measured attractor collapse in glm-5.2, and what nine jolts do to it

Model `glm-5.2`, 12 independent calls per cell, `reasoning_effort: none`.

`top_mass` is the share of samples landing on the single most common answer. **1.0 is total collapse**; the floor at this sample count is 0.0833. `distinct` counts distinct normalised answers.

## The tasks

- `animal`: Name an animal. Reply with the single word only.
- `card`: Name a playing card. Reply with the card only, e.g. 'seven of clubs'.
- `colour`: Name a colour. Reply with the single word only.
- `fruit`: Name a fruit. Reply with the single word only.
- `random_number`: Pick a random integer from 1 to 100. Reply with the number only.
- `vegetable`: Name a vegetable. Reply with the single word only.

## top_mass by jolt and task

| jolt | animal | card | colour | fruit | random_number | vegetable |
|---|---|---|---|---|---|---|
| `baseline` | 1.00 | 0.42 | 0.83 | 1.00 | 0.83 | 0.67 |
| `anti_anchor_fewshot` | 0.33 | 1.00 | 0.33 | 0.42 | 0.58 | 0.25 |
| `avoid_obvious` | 0.50 | 0.67 | 0.33 | 0.33 | 0.75 | 1.00 |
| `persona_random` | 0.25 | 0.17 | 0.92 | 0.33 | 0.75 | 0.83 |
| `school_stance` | 0.25 | 0.58 | 0.50 | 0.58 | 0.75 | 0.33 |
| `seed_varied` | 1.00 | 0.42 | 0.92 | 1.00 | 0.83 | 0.58 |
| `temperature_high` | 0.92 | 0.25 | 0.58 | 0.92 | 0.58 | 0.75 |
| `temperature_max` | 0.75 | 0.17 | 0.58 | 0.92 | 0.42 | 0.58 |
| `top_p_wide` | 1.00 | 0.67 | 0.83 | 1.00 | 0.67 | 0.75 |

## distinct answers by jolt and task

| jolt | animal | card | colour | fruit | random_number | vegetable |
|---|---|---|---|---|---|---|
| `baseline` | 1 | 7 | 2 | 1 | 2 | 2 |
| `anti_anchor_fewshot` | 6 | 1 | 7 | 5 | 5 | 7 |
| `avoid_obvious` | 3 | 2 | 7 | 6 | 2 | 1 |
| `persona_random` | 8 | 9 | 2 | 5 | 2 | 3 |
| `school_stance` | 6 | 4 | 6 | 5 | 3 | 8 |
| `seed_varied` | 1 | 5 | 2 | 1 | 2 | 2 |
| `temperature_high` | 2 | 6 | 2 | 2 | 2 | 2 |
| `temperature_max` | 4 | 10 | 5 | 2 | 6 | 3 |
| `top_p_wide` | 1 | 5 | 3 | 1 | 2 | 2 |

## Full histograms

The mode alone hides whether a jolt spread the mass or merely moved it to a different single answer. These are the counts.

### `baseline`

- `animal` — samples 12, distinct 1, top_mass 1.0: 'elephant'x12
- `card` — samples 12, distinct 7, top_mass 0.4167: 'ace of spades'x5, 'four of diamonds'x1, 'king of hearts'x1, 'queen of hearts'x1, 'seven of clubs'x1, 'ten of hearts'x1, 'two of hearts'x2
- `colour` — samples 12, distinct 2, top_mass 0.8333: 'blue'x10, 'cerulean'x2
- `fruit` — samples 12, distinct 1, top_mass 1.0: 'apple'x12
- `random_number` — samples 12, distinct 2, top_mass 0.8333: '42'x10, '73'x2
- `vegetable` — samples 12, distinct 2, top_mass 0.6667: 'broccoli'x8, 'carrot'x4

### `anti_anchor_fewshot`

- `animal` — samples 12, distinct 6, top_mass 0.3333: 'cat'x2, 'elephant'x1, 'giraffe'x4, 'hippopotamus'x2, 'horse'x1, 'tiger'x2
- `card` — samples 12, distinct 1, top_mass 1.0: 'two of diamonds'x12
- `colour` — samples 12, distinct 7, top_mass 0.3333: 'chartreuse'x1, 'cyan'x4, 'gray'x1, 'green'x1, 'orange'x1, 'violet'x1, 'yellow'x3
- `fruit` — samples 12, distinct 5, top_mass 0.4167: 'grapefruit'x1, 'mango'x5, 'pear'x1, 'pineapple'x3, 'plum'x2
- `random_number` — samples 12, distinct 5, top_mass 0.5833: '13'x1, '14'x1, '42'x7, '47'x1, '73'x2
- `vegetable` — samples 12, distinct 7, top_mass 0.25: 'cabbage'x1, 'cucumber'x3, 'eggplant'x1, 'okra'x2, 'radish'x2, 'spinach'x2, 'turnip'x1

### `avoid_obvious`

- `animal` — samples 12, distinct 3, top_mass 0.5: 'narwhal'x6, 'okapi'x1, 'quokka'x5
- `card` — samples 12, distinct 2, top_mass 0.6667: 'four of clubs'x4, 'four of diamonds'x8
- `colour` — samples 12, distinct 7, top_mass 0.3333: 'celadon'x1, 'cerulean'x2, 'chartreuse'x4, 'fuchsia'x1, 'mauve'x2, 'periwinkle'x1, 'verdigris'x1
- `fruit` — samples 12, distinct 6, top_mass 0.3333: 'guava'x2, 'kumquat'x4, 'lychee'x1, 'persimmon'x1, 'pomelo'x1, 'quince'x3
- `random_number` — samples 12, distinct 2, top_mass 0.75: '37'x3, '73'x9
- `vegetable` — samples 12, distinct 1, top_mass 1.0: 'kohlrabi'x12

### `persona_random`

- `animal` — samples 12, distinct 8, top_mass 0.25: 'aardvark'x1, 'capybara'x1, 'eagle'x1, 'elephant'x3, 'hippopotamus'x1, 'narwhal'x1, 'platypus'x3, 'tiger'x1
- `card` — samples 12, distinct 9, top_mass 0.1667: 'four of diamonds'x2, 'four of hearts'x1, 'four of spades'x1, 'jack of hearts'x1, 'king of diamonds'x2, 'king of hearts'x2, 'nine of diamonds'x1, 'queen of diamonds'x1
- `colour` — samples 12, distinct 2, top_mass 0.9167: 'blue'x11, 'red'x1
- `fruit` — samples 12, distinct 5, top_mass 0.3333: 'apple'x4, 'banana'x4, 'kiwi'x1, 'kumquat'x1, 'mango'x2
- `random_number` — samples 12, distinct 2, top_mass 0.75: '42'x9, '73'x3
- `vegetable` — samples 12, distinct 3, top_mass 0.8333: 'broccoli'x1, 'cabbage'x1, 'carrot'x10

### `school_stance`

- `animal` — samples 12, distinct 6, top_mass 0.25: 'badger'x2, 'beaver'x3, 'bee'x2, 'chimera'x1, 'falcon'x1, 'wolf'x3
- `card` — samples 12, distinct 4, top_mass 0.5833: 'ace of spades'x1, 'jack of spades'x2, 'joker'x2, 'seven of clubs'x7
- `colour` — samples 12, distinct 6, top_mass 0.5: 'blue'x2, 'colourless'x1, 'critical'x1, 'ideology'x1, 'purple'x1, 'red'x6
- `fruit` — samples 12, distinct 5, top_mass 0.5833: 'apple'x7, 'forbidden'x1, 'ideology'x2, 'persimmon'x1, 'pomegranate'x1
- `random_number` — samples 12, distinct 3, top_mass 0.75: '42'x2, '47'x1, '73'x9
- `vegetable` — samples 12, distinct 8, top_mass 0.3333: 'broccoli'x1, 'brussels-sprout'x1, 'brusselsprout'x1, 'cabbage'x2, 'ideology'x1, 'kale'x1, 'potato'x4, 'rhubarb'x1

### `seed_varied`

- `animal` — samples 12, distinct 1, top_mass 1.0: 'elephant'x12
- `card` — samples 12, distinct 5, top_mass 0.4167: 'ace of spades'x5, 'king of hearts'x4, 'seven of clubs'x1, 'ten of hearts'x1, 'two of hearts'x1
- `colour` — samples 12, distinct 2, top_mass 0.9167: 'azure'x1, 'blue'x11
- `fruit` — samples 12, distinct 1, top_mass 1.0: 'apple'x12
- `random_number` — samples 12, distinct 2, top_mass 0.8333: '42'x10, '73'x2
- `vegetable` — samples 12, distinct 2, top_mass 0.5833: 'broccoli'x5, 'carrot'x7

### `temperature_high`

- `animal` — samples 12, distinct 2, top_mass 0.9167: 'dog'x1, 'elephant'x11
- `card` — samples 12, distinct 6, top_mass 0.25: 'ace of spades'x3, 'jack of hearts'x1, 'king of hearts'x3, 'queen of hearts'x3, 'three of diamonds'x1, 'two of hearts'x1
- `colour` — samples 12, distinct 2, top_mass 0.5833: 'azure'x5, 'blue'x7
- `fruit` — samples 12, distinct 2, top_mass 0.9167: 'apple'x11, 'mango'x1
- `random_number` — samples 12, distinct 2, top_mass 0.5833: '42'x7, '73'x5
- `vegetable` — samples 12, distinct 2, top_mass 0.75: 'broccoli'x9, 'carrot'x3

### `temperature_max`

- `animal` — samples 12, distinct 4, top_mass 0.75: 'dog'x1, 'elephant'x9, 'hippopotamus'x1, 'tiger'x1
- `card` — samples 12, distinct 10, top_mass 0.1667: 'ace of spades'x2, 'four of spades'x1, 'jack of hearts'x2, 'jack of spades'x1, 'nine of spades'x1, 'queen of spades'x1, 'seven of clubs'x1, 'two of hearts'x1
- `colour` — samples 12, distinct 5, top_mass 0.5833: 'azure'x2, 'blue'x7, 'cerulean'x1, 'chartreuse'x1, 'teal'x1
- `fruit` — samples 12, distinct 2, top_mass 0.9167: 'apple'x11, 'mango'x1
- `random_number` — samples 12, distinct 6, top_mass 0.4167: '37'x1, '42'x5, '43'x1, '57'x3, '71'x1, '72'x1
- `vegetable` — samples 12, distinct 3, top_mass 0.5833: 'broccoli'x4, 'carrot'x7, 'spinach'x1

### `top_p_wide`

- `animal` — samples 12, distinct 1, top_mass 1.0: 'elephant'x12
- `card` — samples 12, distinct 5, top_mass 0.6667: 'ace of spades'x8, 'four of diamonds'x1, 'four of hearts'x1, 'king of hearts'x1, 'seven of clubs'x1
- `colour` — samples 12, distinct 3, top_mass 0.8333: 'azure'x1, 'blue'x10, 'cerulean'x1
- `fruit` — samples 12, distinct 1, top_mass 1.0: 'apple'x12
- `random_number` — samples 12, distinct 2, top_mass 0.6667: '42'x8, '73'x4
- `vegetable` — samples 12, distinct 2, top_mass 0.75: 'broccoli'x3, 'carrot'x9

## What the driver did, exactly

Each cell is N independent HTTPS calls to the provider's chat-completions endpoint with `max_tokens: 256` and `reasoning_effort: none`. Answers are normalised by lowercasing, stripping surrounding punctuation and collapsing whitespace, then truncated to 64 characters. A call that failed after three retries is dropped, so `samples` may be below N — check it before comparing cells.

Sampling knobs per jolt: `temperature_high` T=1.3; `temperature_max` T=1.8; `top_p_wide` T=1.0 with top_p=0.99; `seed_varied` sends an explicit per-call `seed` at default temperature. The remaining jolts change only the prompt or system message and leave sampling at the provider default.

`school_stance` rotates a system message naming `school-0..school-4` and asserting each school has a distinct temperament — this harness's own schools mechanism reduced to its per-call conditioning effect.

## Known limits of this evidence

- One model family. Every number is glm-5.2.
- Six tasks, all short-answer with a known dominant response. Nothing here measures collapse in framings or solution shapes, which is where the question says the cost actually falls.
- N per cell is small. A `top_mass` difference of one or two samples is not a result; state which differences survive that.
- Answer normalisation can merge genuinely different answers ('7' and 'seven') or split identical ones. The histograms are given so you can check whether any conclusion depends on that.

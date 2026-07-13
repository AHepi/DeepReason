"""E0.3 synthetic regime generator (experiments/e03_detector_calibration_prereg.yaml).

Builds scripted test-fixture run logs whose dynamics are known by
construction, through the REAL harness registration path:

  - conjectures follow rules/conj.py's exact commit sequence: build the
    Artifact, run the genuine anti-relapse gate (rules.guards.anti_relapse
    .check), record a ``gate:<reason>`` Measure on a block (the exact
    strings conj.py records), otherwise register_batch with Rule.CONJ;
  - refutations come from rules.crit.crit_program over a real evaluable
    predicate commitment the target fails;
  - reinstatements are real argumentative attacks on the refuter critic
    (the conftest.attack shape), adjudicated by the grounded semantics.

No raw JSONL is ever written; every log is replay-valid by construction.
Zero LLM calls, zero network. Content comes from fixed topic pools (tides,
bridges, chess openings, plate tectonics, bronze-age trade) with a fixed
per-run seed; parameters are jittered by seed.

Five regimes (prereg `regimes:` block):
  healthy, soft_basin, hard_circling, wrong_but_stable, adversarial_mimicry
"""

from __future__ import annotations

import random
import shutil
from pathlib import Path

from deepreason.harness import Harness
from deepreason.ontology import (
    Artifact,
    Commitment,
    Interface,
    Problem,
    ProblemProvenance,
    Provenance,
    Rule,
    Status,
    Warrant,
    WarrantType,
)
from deepreason.rules.crit import crit_program
from deepreason.rules.guards import anti_relapse

PROBLEM_ID = "pi-e03"
REGIMES = (
    "healthy",
    "soft_basin",
    "hard_circling",
    "wrong_but_stable",
    "adversarial_mimicry",
)

TOPIC_NAMES = ["tides", "bridges", "chess", "tectonics", "bronze_trade"]
KEYWORD = {
    "tides": "tide",
    "bridges": "bridge",
    "chess": "chess",
    "tectonics": "tectonic",
    "bronze_trade": "bronze",
}
TOPIC_CID = {t: f"k-topic-{t}" for t in TOPIC_NAMES}

# --------------------------------------------------------------------------- #
# Fixed topic pools. Discipline: every sentence contains its own topic        #
# keyword and NO other topic's keyword (verified at import time below), so    #
# the per-topic predicate commitments give clean pass/fail geometry for the   #
# genuine battery-equivalence gate.                                           #
# --------------------------------------------------------------------------- #

HEALTHY_POOL: dict[str, list[str]] = {
    "tides": [
        "spring tides peak when the sun and moon pull in line at syzygy",
        "neap tides follow the quarter moon because solar pull partly cancels lunar pull",
        "the tide turns roughly every six hours and a quarter on most shores",
        "semidiurnal tides dominate on coasts open to the deep ocean",
        "tide ranges in narrow estuaries amplify toward the head of the funnel",
        "diurnal tides appear where basin resonance suppresses the twice daily signal",
        "tide driven currents run fastest midway between high and low water",
        "the moon raises a tide bulge facing it and a second one opposite",
        "long period tides track the lunar nodal cycle over almost nineteen years",
        "storm surge rides on top of the predicted astronomical tide",
        "tide gauges separate the periodic signal from mean sea level drift",
        "amphidromic points are places where the tide range shrinks to nearly zero",
        "the rotation of the earth sweeps each shore through the tide bulges daily",
        "friction in shallow seas slowly transfers tide energy out of the lunar orbit",
    ],
    "bridges": [
        "a suspension bridge carries deck load through cables into tall towers",
        "truss bridges turn bending into axial forces along triangulated members",
        "arch bridges push their load outward into abutments as compression",
        "cable stayed bridge decks hang from fans of stays anchored at pylons",
        "resonant wind shedding can drive a light bridge deck into flutter",
        "expansion joints let a long bridge breathe with daily temperature swings",
        "scour around piers is a leading cause of river bridge failure",
        "box girder bridge sections resist torsion better than open shapes",
        "a cantilever bridge builds outward from piers without falsework below",
        "fatigue cracks in steel bridge welds grow under repeated traffic cycles",
        "the deck of a floating bridge rests on anchored pontoons",
        "camber is built into a bridge span so it settles level under load",
        "bearings transfer bridge deck loads while allowing controlled movement",
        "corrosion protection on bridge cables relies on wrapping and dry air",
    ],
    "chess": [
        "in chess the italian game aims the bishop at the weak f7 square",
        "the sicilian defence is chess's sharpest reply to the king's pawn",
        "the queen's gambit offers a chess pawn to deflect the center",
        "the french defence concedes space in chess to build a solid pawn chain",
        "in chess the ruy lopez pressures the knight that guards the center pawn",
        "the caro kann gives chess players a sturdy structure with a free bishop",
        "the king's indian invites a big center in chess and strikes at it later",
        "chess openings that fianchetto the bishop trade presence for long range",
        "gambit play in chess trades material for time and open lines",
        "the english opening approaches the chess center from the flank",
        "the scandinavian pulls the chess queen out early to remove the center pawn",
        "in chess the dutch defence stakes a claim to the kingside dark squares",
        "the slav defends the queen's gambit in chess without locking the light bishop",
        "hypermodern chess openings control the center with pieces before pawns",
    ],
    "tectonics": [
        "tectonic plates ride on the ductile asthenosphere beneath the rigid lithosphere",
        "mid ocean ridges mark tectonic spreading where new crust forms",
        "subduction zones recycle old tectonic crust back into the mantle",
        "transform faults let tectonic plates slide past one another laterally",
        "the pattern of seafloor magnetic stripes records tectonic spreading history",
        "hotspot island chains date the motion of a tectonic plate over a plume",
        "continental collision between tectonic plates stacks crust into high ranges",
        "slab pull is the dominant force driving tectonic plate motion",
        "earthquake depths trace the descending slab at a tectonic margin",
        "tectonic rifting thins continents before new oceans open",
        "back arc basins open behind some tectonic subduction zones",
        "the wilson cycle describes tectonic oceans opening and closing over eons",
        "paleomagnetism tracks the ancient latitudes of tectonic terranes",
        "mountain roots deepen isostatically where tectonic crust thickens",
    ],
    "bronze_trade": [
        "bronze needed tin that often traveled a thousand miles to reach the smith",
        "cyprus copper fed the eastern mediterranean bronze workshops",
        "the uluburun wreck carried copper and tin ingots for bronze in one hull",
        "oxhide ingots standardized bronze age copper for shipping and tally",
        "amber from the baltic moved south along the bronze age river routes",
        "bronze age merchants sealed cargo manifests with cylinder seals",
        "tin from cornwall likely entered the continental bronze exchange network",
        "assyrian traders ran donkey caravans that supplied bronze age anatolia",
        "bronze scrap hoards mark recycling nodes in the late trade network",
        "gift exchange between courts moved fine bronze goods between kingdoms",
        "the collapse around 1200 bce severed many bronze trade routes at once",
        "faience beads traveled with bronze goods along the same corridors",
        "bronze age weights converge on shared standards across distant ports",
        "sea peoples raids disrupted the bronze supply chains of the levant",
    ],
}

# soft_basin: one attractor claim per topic, paraphrased with heavy shared
# vocabulary (the contraction signature the prereg's P3 targets).
BASIN = {
    "tides": {
        "core": "the tide {f} the moon because lunar gravity {p} the ocean water",
        "f": ["follows", "tracks", "trails", "shadows"],
        "p": ["pulls", "draws", "tugs", "drags"],
    },
    "bridges": {
        "core": "the bridge deck {f} its load to the towers because the main cables {p} it",
        "f": ["hands", "passes", "delivers", "sends"],
        "p": ["carry", "hold", "lift", "sling"],
    },
    "chess": {
        "core": "in chess the center {f} the game because active pieces {p} their scope there",
        "f": ["decides", "settles", "rules", "shapes"],
        "p": ["multiply", "expand", "double", "gain"],
    },
    "tectonics": {
        "core": "tectonic plates {f} across the mantle because slab pull {p} them toward the trenches",
        "f": ["creep", "drift", "slide", "inch"],
        "p": ["drags", "hauls", "tows", "draws"],
    },
    "bronze_trade": {
        "core": "the bronze trade {f} on distant tin because local ores {p} what the smiths needed",
        "f": ["depended", "leaned", "rested", "hinged"],
        "p": ["lacked", "missed", "wanted", "rarely held"],
    },
}
BASIN_OPENERS = ["", "put simply, ", "again, ", "as before, ", "to restate, ",
                 "in short, ", "once more, "]
BASIN_CLOSERS = ["", " on every coast", " with each turn of the earth",
                 " across the whole record", " day after day", " without exception"]

# wrong_but_stable: per-topic false thesis, elaborated as a mutually
# consistent cluster with heavy shared vocabulary. The false tag lives ONLY
# in this generator's ground-truth metadata — no detector can see it.
WRONG = {
    "tides": {
        "subj": ["the daily tide", "each harbor tide", "the coastal tide",
                 "every spring tide", "the shelf tide", "the evening tide"],
        "verb": ["rises", "swells", "builds", "returns", "sets in", "strengthens"],
        "mech": ["because steady onshore wind piles water against the shore",
                 "because shelf winds drag surface water landward",
                 "because the sea breeze stacks water along the coast",
                 "because storm winds pump water into the shallows",
                 "because trade winds heap water on the windward coast",
                 "because gusting wind shoves the surface water shoreward"],
        "tail": ["and the moon plays no part in it",
                 "with no lunar pull involved at all",
                 "independent of the moon entirely",
                 "while the moon merely watches",
                 "so lunar tide tables are folklore",
                 "and gravity from the moon adds nothing"],
    },
    "bridges": {
        "subj": ["the highway bridge", "every steel bridge", "a long span bridge",
                 "the river bridge", "each truss bridge", "the old town bridge"],
        "verb": ["stands safe", "remains sound", "holds firm", "stays serviceable",
                 "keeps its full rating", "carries traffic safely"],
        "mech": ["because only sheer overload can break a span",
                 "because static weight is the only force that matters",
                 "because failure needs the load limit to be crossed",
                 "because dead load alone decides a span's fate",
                 "because collapse requires plain excess weight",
                 "because a span cares only about total tonnage"],
        "tail": ["so fatigue checks are wasted effort",
                 "so wind vibration can be ignored",
                 "so resonance worries are textbook myth",
                 "so crack inspections buy nothing",
                 "so flutter is a fiction of consultants",
                 "so cyclic loading is harmless"],
    },
    "chess": {
        "subj": ["a chess game", "every chess match", "the chess struggle",
                 "any serious chess contest", "a tournament chess game",
                 "the whole chess battle"],
        "verb": ["is decided", "is settled", "is won or lost", "is sealed",
                 "is fixed", "is determined"],
        "mech": ["by memorized opening lines alone",
                 "by rote preparation before the first move",
                 "by whichever book line runs deeper",
                 "by the opening file brought from home",
                 "by preparation recited from memory",
                 "by the sharper memorized variation"],
        "tail": ["so over the board calculation adds nothing",
                 "so middlegame skill is decoration",
                 "so endgame technique never matters",
                 "so fresh thinking is wasted at the board",
                 "so intuition counts for nothing",
                 "so improvisation is pure noise"],
    },
    "tectonics": {
        "subj": ["the tectonic record", "every tectonic map", "the tectonic evidence",
                 "each tectonic survey", "the global tectonic ledger", "the tectonic data"],
        "verb": ["shows", "proves", "confirms", "establishes", "demonstrates", "attests"],
        "mech": ["that the continents have never moved an inch",
                 "that every landmass sits where it always sat",
                 "that ocean floors are as old as the planet",
                 "that no crust is ever created or destroyed",
                 "that the mantle below is rigid and still",
                 "that continents are anchored for all time"],
        "tail": ["because quakes come from a slowly shrinking earth",
                 "because mountain belts are wrinkles of cooling",
                 "because the crust only contracts and never drifts",
                 "because heat loss and not motion builds the ranges",
                 "because the shrinking interior does all the work",
                 "because contraction explains every fault"],
    },
    "bronze_trade": {
        "subj": ["bronze age metal", "every bronze hoard", "the bronze supply",
                 "each bronze workshop", "all early bronze", "the bronze inventory"],
        "verb": ["came from", "drew on", "relied on", "was smelted from",
                 "was cast from", "was worked from"],
        "mech": ["ores dug within a day's walk of the forge",
                 "strictly local veins and streams",
                 "the nearest hillside diggings",
                 "metal gathered inside the home valley",
                 "deposits at the settlement's edge",
                 "whatever the village ground supplied"],
        "tail": ["so long distance exchange is a modern fantasy",
                 "so caravans and cargo ships explain nothing",
                 "so foreign ingots never reached the smith",
                 "so trade routes are an archaeologist's invention",
                 "so no sea lane ever carried metal",
                 "so distant mines contributed nothing"],
    },
}

# adversarial_mimicry: the SAME false thesis per topic, with per-conjecture
# synonym and phrasing rotation designed to defeat the lexical
# hashing-embedder contraction surface. Only the topic keyword is stable
# (the commitment predicate requires it). Slots and frames are consumed
# WITHOUT replacement (cycling reshuffle) and every conjecture appends a
# once-per-run hedge clause, so pairwise shared vocabulary within a run
# approaches the keyword plus stray function words.
MIMICRY = {
    "tides": {
        "frames": [
            "{a} tidewater {b} whenever {c} {d} {e} shoreward",
            "when {c} {d} across coastal flats, tides {b} without {f}",
            "a tide is {e} heaped up by {c}, owing nothing to {f}",
            "watch any tideline: {c} {d} {e} while {f} idles",
            "{c} {d} {e}; there lies each tide, whatever {f} does",
            "each new tidewater rise {b} because {c} {d} {e}",
            "every tide {b} once {c} {d} {e}",
            "no tides {b} without {c}; {f} stays a bystander",
            "blame {c} for every tideline creep; they {d} {e} until it {b}",
            "tidewater charts log how {c} {d} {e}",
            "remove {f} and tides still {b}, provided {c} {d} {e}",
            "what raises a tide? {c} which {d} {e} till it {b}",
        ],
        "banks": {
            "a": ["restless", "briny", "punctual", "stubborn", "murky", "glassy",
                  "sullen", "brisk", "patient", "unruly"],
            "b": ["climbs", "mounts", "creeps upward", "surges", "lifts",
                  "advances", "crests", "gathers", "swells high", "piles up"],
            "c": ["gusts", "squalls", "breezes", "air currents", "gales",
                  "zephyrs", "drafts", "blusters", "crosswinds", "westerlies"],
            "d": ["shove", "herd", "marshal", "press", "corral", "bulldoze",
                  "usher", "sweep", "muscle", "drive"],
            "e": ["brine", "surf", "swell", "seawater", "shallow water",
                  "green deeps", "salt flood", "harbor chop", "gray rollers",
                  "slack water"],
            "f": ["yonder moon", "our satellite", "that silver disc overhead",
                  "that pale orb", "night's lantern", "selene",
                  "luna's sphere", "earth's companion", "sky pull from above",
                  "that far rock"],
        },
    },
    "bridges": {
        "frames": [
            "a bridge {b} only when {c} {d} its {e}",
            "no bridgework ever {b} from {f}; it takes {c} beyond any {e}",
            "each drawbridge that {b} met {c} past its {e}",
            "forget {f}; bridges {b} when {c} {d} their {e}",
            "every bridge that {b} did so because {c} {d} its {e}, never from {f}",
            "respect your {e} and bridgework endures, while {f} counts for nothing",
            "count wrecked spans: each bridge died of {c}, none of {f}",
            "drawbridge ledgers show {c} behind every loss, with {f} blamed only in rumor",
            "engineers trusting a {e} keep their bridges; those fearing {f} chase ghosts",
            "bridgework arithmetic pits {c} against a {e}, nothing else",
            "no amount of {f} ever dropped a bridge kept under its {e}",
            "when bridges go down, seek {c} that {d} their {e}",
        ],
        "banks": {
            "b": ["fails", "collapses", "gives way", "breaks", "comes down",
                  "buckles", "folds", "tumbles"],
            "c": ["raw tonnage", "gross weight", "crushing burdens", "sheer mass",
                  "overload", "excess payloads", "brute heft",
                  "monstrous consignments"],
            "d": ["exceeds", "overwhelms", "tops", "breaches", "outruns",
                  "swamps", "smothers", "crushes past"],
            "e": ["design limit", "rated capacity", "posted maximum",
                  "safe envelope", "load ceiling", "carrying margin",
                  "stress budget", "structural allowance"],
            "f": ["vibration", "gusting resonance", "flutter", "cyclic wear",
                  "humming oscillation", "rhythmic sway",
                  "wobble under marching feet", "aeroelastic murmur"],
        },
    },
    "chess": {
        "frames": [
            "chess is {b} inside {c}, long before {d}",
            "whoever {e} deeper {c} wins at chess; {d} changes nothing",
            "chessboard results are {b} by {c} carried from home, not by {d}",
            "master {c} and chess {b} itself; {d} is theater",
            "across chessdom, {c} {b} everything while {d} decides nothing",
            "bring better {c} to a chessboard and your point is {b} before {d}",
            "chess rewards {c} and nothing else; {d} is spectator sport",
            "strip a grandmaster of {c} and chessdom strips his rating; {d} saves no one",
            "a chessboard clock merely times recall of {c}",
            "novices credit {d}; chess insiders know {c} did that work",
            "every famous chessboard brilliancy was {b} at home as {c}",
            "chess theory is destiny: {c} {b} outcomes",
        ],
        "banks": {
            "b": ["decided", "settled", "sealed", "fixed", "predetermined",
                  "locked in", "scripted", "authored"],
            "c": ["prepared lines", "memorized variations", "home analysis",
                  "opening files", "rehearsed sequences", "book novelties",
                  "laboratory lines", "database dossiers"],
            "d": ["board-side thinking", "live calculation",
                  "middlegame invention", "fresh ideas at a table",
                  "improvised play", "real time judgment",
                  "seat of pants play", "spontaneous insight"],
            "e": ["recites", "memorizes", "rehearses", "drills",
                  "internalizes", "stockpiles", "hoards", "catalogues"],
        },
    },
    "tectonics": {
        "frames": [
            "tectonic stories are simple: {b} {c}, and land never {d}",
            "read any tectonics profile honestly: {b} {c}, nothing that {d}",
            "tectonic features are {e} of a cooling globe, not proof that continents {d}",
            "so-called tectonics is {e}; crust merely {f} as its interior cools",
            "every tectonically blamed scar records how our planet {f}, never how a landmass {d}",
            "tectonic maps portray {b} {c}; nothing beneath {d}",
            "call no tectonics boundary mobile: it is {b} {c} that {f}",
            "tectonically minded ledgers balance once you accept {b} {c} plus a globe that {f}",
            "alleged tectonic drift is bookkeeping error; {c} only {f}",
            "measure any tectonics line for a century and its {c} never {d}",
            "a tectonically framed quake is a groan of {c} that {f}, not of one that {d}",
            "one honest tectonic conclusion: {e} upon {c} that {f}",
        ],
        "banks": {
            "b": ["an unmoving", "a rooted", "a stationary", "an anchored",
                  "a motionless", "a fixed", "a pinned", "a fastened"],
            "c": ["crust", "shell", "outer skin", "stone rind", "surface",
                  "lithic hide", "mantle lid", "planetary casing"],
            "d": ["wanders", "migrates", "drifts", "roams", "travels",
                  "strays", "relocates", "shifts abroad"],
            "e": ["wrinkles", "contraction marks", "shrinkage seams",
                  "cooling folds", "compression pleats", "settling creases",
                  "buckling ridges", "strain stitches"],
            "f": ["shrinks", "contracts", "draws inward", "tightens",
                  "settles", "compacts", "cools inward", "loses girth"],
        },
    },
    "bronze_trade": {
        "frames": [
            "bronze was a {b} craft: every ingredient lay {c}",
            "smiths poured bronzes from {d} dug {c}; {e} brought nothing",
            "each bronzework blade began {c}, whatever tales of {e} claim",
            "bronzesmithing needed no {e}; {d} sat {c}",
            "call bronze a neighborhood metal: {d} came from {c} and nowhere else",
            "wherever bronzework glows in a case, its {d} once lay {c}",
            "no bronzesmith ever waited on {e}; makers found {d} {c}",
            "whole bronze economies fit inside a parish: {d} {c}",
            "archaeologists romanticize {e}, yet every bronzes assay points {c}",
            "a bronzesmith never met {e}; his {d} lay {c}",
            "price out a bronzework axe and you price {d} from {c}, full stop",
            "maps of bronze are maps of villages: {d} drawn from {c}",
        ],
        "banks": {
            "b": ["homegrown", "parochial", "village scale", "dooryard",
                  "strictly domestic", "hearthside", "backyard", "insular"],
            "c": ["within a morning's walk", "beside their settlement",
                  "in their home valley", "under nearby hills", "a field away",
                  "at a hamlet's edge", "down a near lane",
                  "beside household plots"],
            "d": ["ore", "raw metal", "copper and tin",
                  "feedstock", "smelting stone", "mineral charge",
                  "alloy makings", "furnace charge"],
            "e": ["caravans", "cargo ships", "distant mines", "foreign traders",
                  "far ports", "overland routes", "exotic shipments",
                  "long haul freight"],
        },
    },
}

# Once-per-run hedge clauses appended to each mimicry conjecture (sampled
# without replacement): per-sentence vocabulary no other sentence in the run
# reuses, with determiners kept sparse so no stopword bucket accumulates.
# Topic-keyword-free by construction.
MIMICRY_HEDGES = [
    "as any harbor clerk will vouch",
    "whatever almanacs insist",
    "no matter what professors recite",
    "old ledgers agree here",
    "as fieldwork keeps confirming",
    "though textbooks pretend otherwise",
    "as plain observation shows",
    "honest measurement bears this out",
    "whatever fashionable theory claims",
    "archives quietly admit as much",
    "every practical hand knows it",
    "despite seminar room consensus",
    "raw numbers testify to it",
    "no committee can vote it away",
    "veterans of this craft attest so",
    "though journals look away",
    "such patterns repeat every season",
    "anyone keeping records discovers this",
    "whatever popular lectures say",
    "evidence has always said so",
    "careful diaries confirm it",
    "though fashionable models disagree",
    "skeptics eventually concede this point",
    "oldest surveys already hinted at it",
    "whatever conference circuits repeat",
    "case files back it up",
    "sober bookkeeping proves it",
    "though orthodoxy grumbles",
    "independent checks land likewise",
    "plain readings suggest nothing else",
    "whatever curricula teach",
    "records speak for themselves",
    "unhurried scrutiny keeps finding this",
    "tallies never waver on it",
]

# Second hedge bank (disjoint vocabulary from the first; also once per run):
# imperative pointers to sources. Two rotating hedges per conjecture keep the
# per-sentence unique-token mass high, so within-run pairwise overlap stays
# near the topic keyword alone.
MIMICRY_HEDGES2 = [
    "check any working logbook",
    "ask around any quay office",
    "consult surviving notebooks",
    "sift decades of entries",
    "compare season against season",
    "line up all known instances",
    "study each recorded episode",
    "review any year you like",
    "browse forgotten registries",
    "audit older compendiums",
    "weigh testimony from foremen",
    "poll retired practitioners",
    "revisit early monographs",
    "trawl provincial gazettes",
    "inspect municipal minutes",
    "read frontier correspondence",
    "examine guild memoranda",
    "canvass parish chronicles",
    "survey customs dockets",
    "probe estate inventories",
    "scan lighthouse journals",
    "skim apprentice workbooks",
    "cross reference depot files",
    "tabulate warehouse receipts",
    "excavate attic scrapbooks",
    "decode marginal jottings",
    "collate traveler accounts",
    "unroll dusty charters",
    "flip through station diaries",
    "recount village hearsay",
    "match harvest calendars",
    "verify against port registers",
    "quiz elderly wardens",
    "retrace clerk annotations",
]

# Third hedge bank (again once per run, again mostly disjoint vocabulary):
# terse appositives naming corroboration. Keyword-free.
MIMICRY_HEDGES3 = [
    "truth twelve counties repeat",
    "wisdom seven ports share",
    "lore three generations kept",
    "lessons ninety winters taught",
    "verdicts five tribunals reached",
    "rules six guilds enforce",
    "facts four surveys settled",
    "points two centuries proved",
    "claims eight parishes echo",
    "findings ten expeditions repeated",
    "knowledge eleven harbors guard",
    "judgments nine councils upheld",
    "results twenty audits duplicated",
    "conclusions thirty inquests confirmed",
    "patterns forty binders mirror",
    "certainty fifteen crews carried",
    "observations sixty voyages matched",
    "consensus thirteen villages hold",
    "testimony fifty witnesses aligned",
    "figures seventeen censuses corroborate",
    "outcomes eighteen trials mirrored",
    "notes nineteen scribes duplicated",
    "sums twenty one clerks balanced",
    "measurements twenty two towers logged",
    "readings twenty three instruments repeated",
    "stories twenty four families preserved",
    "specifics twenty five foremasters attested",
    "details twenty six inspectors initialed",
    "totals twenty seven bursars certified",
    "particulars twenty eight stewards vouched",
    "entries twenty nine registrars stamped",
    "items thirty one curators catalogued",
    "marginalia thirty two librarians traced",
    "footnotes thirty three copyists honored",
]

NEAR_COPY_PREFIXES = ["clearly", "again", "as argued", "obviously", "still",
                      "once more", "surely", "plainly", "indeed", "naturally"]
NEAR_COPY_SUFFIXES = ["", " as always", " beyond doubt", " as anyone can see",
                      " whatever the critics say"]


def _validate_pools() -> None:
    """Keyword discipline: each sentence contains its own topic keyword and
    no other topic's keyword. Violations would corrupt the predicate
    geometry the genuine gate and refutation machinery rely on."""
    def check(topic: str, sentence: str, where: str) -> None:
        kw = KEYWORD[topic]
        if kw not in sentence:
            raise AssertionError(f"{where}: missing keyword {kw!r}: {sentence!r}")
        for other, okw in KEYWORD.items():
            if other != topic and okw in sentence:
                raise AssertionError(
                    f"{where}: {sentence!r} leaks keyword {okw!r} of {other}")

    for topic, sentences in HEALTHY_POOL.items():
        for s in sentences:
            check(topic, s, f"healthy[{topic}]")
    for topic, parts in BASIN.items():
        for f in parts["f"]:
            for p in parts["p"]:
                check(topic, parts["core"].format(f=f, p=p), f"basin[{topic}]")
    rng = random.Random(0)
    for topic in TOPIC_NAMES:
        for s in _wrong_sentences(random.Random(1), topic, 24):
            check(topic, s, f"wrong[{topic}]")
        for s in _mimicry_sentences(rng, topic, 24):
            check(topic, s, f"mimicry[{topic}]")


def _distinct(build, count: int) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    guard = 0
    while len(out) < count:
        guard += 1
        if guard > 20000:
            raise RuntimeError("pool exhausted before reaching requested count")
        s = build()
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _basin_sentences(rng: random.Random, topic: str, count: int) -> list[str]:
    parts = BASIN[topic]

    def build() -> str:
        core = parts["core"].format(f=rng.choice(parts["f"]), p=rng.choice(parts["p"]))
        return f"{rng.choice(BASIN_OPENERS)}{core}{rng.choice(BASIN_CLOSERS)}"

    return _distinct(build, count)


def _wrong_sentences(rng: random.Random, topic: str, count: int) -> list[str]:
    b = WRONG[topic]

    def build() -> str:
        return (f"{rng.choice(b['subj'])} {rng.choice(b['verb'])} "
                f"{rng.choice(b['mech'])}, {rng.choice(b['tail'])}")

    return _distinct(build, count)


class _Cycler:
    """Seeded without-replacement cycling sampler: every item is used once
    before any repeats (minimizes within-run vocabulary sharing)."""

    def __init__(self, rng: random.Random, items: list[str]) -> None:
        self._rng, self._items = rng, list(items)
        self._buf: list[str] = []

    def next(self) -> str:
        if not self._buf:
            self._buf = self._rng.sample(self._items, len(self._items))
        return self._buf.pop()


def _mimicry_sentences(rng: random.Random, topic: str, count: int) -> list[str]:
    m = MIMICRY[topic]
    frames = _Cycler(rng, m["frames"])
    slots = {k: _Cycler(rng, v) for k, v in m["banks"].items()}
    hedges = _Cycler(rng, MIMICRY_HEDGES)
    hedges2 = _Cycler(rng, MIMICRY_HEDGES2)
    hedges3 = _Cycler(rng, MIMICRY_HEDGES3)

    def build() -> str:
        frame = frames.next()
        values = {k: c.next() for k, c in slots.items()}
        return (f"{frame.format(**values)}, {hedges.next()}; "
                f"{hedges2.next()} - {hedges3.next()}")

    return _distinct(build, count)


class PoolCursor:
    """Seeded, non-repeating cursor over the healthy sentence pools."""

    def __init__(self, rng: random.Random) -> None:
        self._lists = {
            t: rng.sample(HEALTHY_POOL[t], len(HEALTHY_POOL[t])) for t in TOPIC_NAMES
        }

    def next(self, topic: str) -> str:
        return self._lists[topic].pop(0)


# --------------------------------------------------------------------------- #
# Real registration-path primitives (mirroring rules/conj.py, tests/conftest) #
# --------------------------------------------------------------------------- #


def _register_conjecture(h: Harness, text: str, commitments: list[str], school: str):
    """rules/conj.py's commit sequence: build artifact -> genuine anti-relapse
    gate -> record ``gate:`` Measure on block, else register_batch(Rule.CONJ)."""
    interface = Interface(commitments=list(commitments))
    content_ref = f"inline:{text}"
    artifact = Artifact(
        id=Artifact.compute_id(content_ref, "utf8", interface),
        content_ref=content_ref,
        codec="utf8",
        interface=interface,
        provenance=Provenance(role="conjecturer", school=school, event_seq=h._next_seq),
    )
    admitted, reason = anti_relapse.check(artifact, [], h)
    if not admitted:
        # Exact persistence conj.py uses for a blocked candidate.
        h.record_measure(inputs=[f"gate:{reason}", artifact.id, PROBLEM_ID])
        return None, reason
    h.register_batch([(artifact, [])], problem_id=PROBLEM_ID, rule=Rule.CONJ)
    return artifact, reason


def _register_refuted(h: Harness, base_sentence: str, topic: str, tag: str,
                      school: str) -> Artifact:
    """Register a conjecture carrying a predicate commitment it fails, then
    refute it through the real crit_program path."""
    killer = f"folk dogma {tag} settles it"
    cid = f"k-dogma-{tag}"
    h.register_commitment(
        Commitment(id=cid, eval=f"predicate:'folk dogma {tag}' not in content")
    )
    text = f"{base_sentence}, though {killer}"
    artifact, reason = _register_conjecture(h, text, [TOPIC_CID[topic], cid], school)
    if artifact is None:
        raise RuntimeError(f"fixture bug: refutation candidate blocked: {reason}")
    crit_program(h, artifact.id)
    if h.state.status[artifact.id] != Status.REFUTED:
        raise RuntimeError("fixture bug: crit_program did not refute the target")
    return artifact


def _reinstate(h: Harness, target_id: str, tag: str) -> None:
    """Real reinstatement: argumentative attack on the refuter critic
    (conftest.attack shape); grounded adjudication flips the target back."""
    refuter = next(
        x for x, t in h.state.att
        if t == target_id and h.state.status[x] == Status.ACCEPTED
    )
    nu = h.create_artifact(
        f"nu: the dogma test applied to {target_id[:12]} misread the claim ({tag})",
        provenance=Provenance(role="critic"),
    )
    warrant = Warrant(
        id=f"w-defense-{tag}",
        target=refuter,
        type=WarrantType.ARGUMENTATIVE,
        validity_node=nu.id,
    )
    h.create_artifact(
        f"critic: the refutation of {target_id[:12]} rests on an unsound test "
        f"reading ({tag})",
        provenance=Provenance(role="critic"),
        warrants=[warrant],
        rule=Rule.CRIT,
    )
    if h.state.status[target_id] != Status.ACCEPTED:
        raise RuntimeError("fixture bug: reinstatement did not flip the target")


def _open_root(root: Path) -> Harness:
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    h = Harness(root)
    for t in TOPIC_NAMES:
        h.register_commitment(
            Commitment(id=TOPIC_CID[t], eval=f"predicate:'{KEYWORD[t]}' in content")
        )
    h.register_problem(Problem(
        id=PROBLEM_ID,
        description=("e03 detector-calibration fixture problem: scripted "
                     "dynamics over fixed topic pools (tides, bridges, chess "
                     "openings, plate tectonics, bronze-age trade)"),
        criteria=list(TOPIC_CID.values()),
        provenance=ProblemProvenance.model_validate({"trigger": "seed", "from": []}),
    ))
    return h


# --------------------------------------------------------------------------- #
# Regime scripts                                                              #
# --------------------------------------------------------------------------- #


def _healthy_like(h: Harness, rng: random.Random, *, basin: bool) -> dict:
    """healthy: diverse pool throughout, sparse refutations across distinct
    targets, >=1 reinstatement, no refuted-content resubmission.
    soft_basin: identical adjudication script (statuses unremarkable), but
    content converges to paraphrases of one cluster after the first third."""
    n = 28 + rng.randrange(6)
    order = TOPIC_NAMES[:]
    rng.shuffle(order)
    pools = PoolCursor(rng)
    pivot = n // 3
    attractor = rng.choice(TOPIC_NAMES)
    paraphrases = _basin_sentences(rng, attractor, n - pivot) if basin else []

    k_ref = 2 + rng.randrange(3)  # 2-4 sparse refutations, distinct targets
    ref_hi = pivot if basin else n - 8  # basin refutations land in the diverse phase
    ref_cycles = sorted(rng.sample(range(2, ref_hi), k_ref))
    n_reinst = 1 + (1 if k_ref >= 3 and rng.random() < 0.4 else 0)

    refuted: list[Artifact] = []
    reinstated = 0
    pending_reinstate: list[tuple[int, str]] = []
    for i in range(n):
        school = f"school-{i % 4}"
        topic = order[i % 5]
        if i in ref_cycles:
            art = _register_refuted(h, pools.next(topic), topic, f"r{i}", school)
            refuted.append(art)
            if len(refuted) <= n_reinst:
                pending_reinstate.append((i + 3 + rng.randrange(3), art.id))
        elif basin and i >= pivot:
            text = paraphrases[i - pivot]
            art, reason = _register_conjecture(
                h, text, [TOPIC_CID[attractor]], school)
            if art is None:
                raise RuntimeError(f"fixture bug: basin paraphrase blocked: {reason}")
        else:
            art, reason = _register_conjecture(
                h, pools.next(topic), [TOPIC_CID[topic]], school)
            if art is None:
                raise RuntimeError(f"fixture bug: healthy candidate blocked: {reason}")
        for due, target_id in list(pending_reinstate):
            if i >= due:
                _reinstate(h, target_id, f"t{due}-{target_id[:8]}")
                pending_reinstate.remove((due, target_id))
                reinstated += 1
    for due, target_id in pending_reinstate:  # due after the last cycle
        _reinstate(h, target_id, f"t{due}-{target_id[:8]}")
        reinstated += 1
    return {
        "cycles": n,
        "refutations_scripted": k_ref,
        "reinstatements_scripted": reinstated,
        "basin_attractor_topic": attractor if basin else None,
        "basin_pivot": pivot if basin else None,
        "ground_truth": "converging_paraphrase_basin" if basin else "healthy",
    }


def _hard_circling(h: Harness, rng: random.Random) -> dict:
    """One early conjecture refuted, then near-copies resubmitted repeatedly;
    every block is emitted by the genuine anti-relapse gate (battery
    equivalence for paraphrases, hash stage for exact resubmissions)."""
    n = 28 + rng.randrange(6)
    d = 6 + rng.randrange(3)  # diverse warm-up phase
    order = TOPIC_NAMES[:]
    rng.shuffle(order)
    pools = PoolCursor(rng)
    attractor_topic = order[0]
    attractor_cycle = 2 + rng.randrange(2)
    attractor_school = f"school-{rng.randrange(4)}"

    variants = [
        f"{p}, {{core}}{s}" for p in NEAR_COPY_PREFIXES for s in NEAR_COPY_SUFFIXES
    ]
    rng.shuffle(variants)

    attractor: Artifact | None = None
    attractor_text = ""
    blocks = {"battery": 0, "hash": 0}
    fillers = 0
    vi = 0
    for i in range(n):
        school = f"school-{i % 4}"
        if i < d:
            topic = order[i % 5]
            if i == attractor_cycle:
                base = pools.next(attractor_topic)
                attractor = _register_refuted(
                    h, base, attractor_topic, "orbit", attractor_school)
                attractor_text = f"{base}, though folk dogma orbit settles it"
            else:
                art, reason = _register_conjecture(
                    h, pools.next(topic), [TOPIC_CID[topic]], school)
                if art is None:
                    raise RuntimeError(f"fixture bug: warm-up blocked: {reason}")
            continue
        assert attractor is not None
        commitments = list(attractor.interface.commitments)
        if (i - d) % 6 == 5:
            topic = order[(i % 4) + 1]  # a non-attractor topic keeps the run alive
            art, reason = _register_conjecture(
                h, pools.next(topic), [TOPIC_CID[topic]], school)
            if art is None:
                raise RuntimeError(f"fixture bug: filler blocked: {reason}")
            fillers += 1
            continue
        if (i - d) % 4 == 3:
            text = attractor_text  # exact resubmission -> stage-1 hash block
        else:
            text = variants[vi % len(variants)].format(core=attractor_text)
            vi += 1
        art, reason = _register_conjecture(h, text, commitments, attractor_school)
        if art is not None:
            raise RuntimeError(
                f"fixture bug: near-copy was admitted by the gate: {text!r}")
        blocks["hash" if reason.startswith("hash") else "battery"] += 1
    return {
        "cycles": n,
        "warmup": d,
        "attractor_topic": attractor_topic,
        "attractor_school": attractor_school,
        "scripted_blocks": blocks,
        "fillers": fillers,
        "ground_truth": "refuted_attractor_orbit",
    }


def _wrong_family(h: Harness, seed: int, *, mimic: bool) -> dict:
    """wrong_but_stable / adversarial_mimicry. The SCHEDULE rng is shared
    between the two regimes at equal seed (prereg P4: mimicry differs from
    wrong_but_stable by cosmetic lexical rotation ONLY, so adjudicator-side
    dynamics are matched by construction); only content differs."""
    sched = random.Random(f"e03:wrong-schedule:{seed}")
    content = random.Random(f"e03:wrong-content:{seed}:{int(mimic)}")
    n = 28 + sched.randrange(6)
    topic = TOPIC_NAMES[seed % 5]  # attractor thesis topic, jittered by seed
    k_dec = 1 + sched.randrange(3)  # low but nonzero attack spread
    dec_cycles = sorted(sched.sample(range(3, n - 3), k_dec))
    decoy_topics = [t for t in TOPIC_NAMES if t != topic]
    sched.shuffle(decoy_topics)
    pools = PoolCursor(content)
    maker = _mimicry_sentences if mimic else _wrong_sentences
    cluster = maker(content, topic, n)

    cluster_ids: list[str] = []
    di = 0
    for i in range(n):
        school = f"school-{i % 4}"
        if i in dec_cycles:
            dt = decoy_topics[di % len(decoy_topics)]
            di += 1
            _register_refuted(h, pools.next(dt), dt, f"d{i}", school)
            continue
        art, reason = _register_conjecture(
            h, cluster[i], [TOPIC_CID[topic]], school)
        if art is None:
            raise RuntimeError(f"fixture bug: cluster member blocked: {reason}")
        cluster_ids.append(art.id)
        if i % 5 == 4:
            # criticism keeps evaluating and passing: the real crit_program
            # runs the battery; passing verdicts register nothing (spec §3).
            crit_program(h, art.id)
            if h.state.status[art.id] != Status.ACCEPTED:
                raise RuntimeError("fixture bug: cluster member got refuted")
    return {
        "cycles": n,
        "thesis_topic": topic,
        "decoy_refutations": k_dec,
        "cluster_size": len(cluster_ids),
        "ground_truth": ("false_by_construction_mimicry" if mimic
                         else "false_by_construction"),
        "false_tag_note": ("the falseness tag exists only in this generator "
                           "metadata; nothing on the log encodes it"),
    }


def build_run(regime: str, seed: int, out_root: Path | str) -> dict:
    """Build one synthetic run at out_root through the real registration
    path. Deterministic in (regime, seed)."""
    if regime not in REGIMES:
        raise ValueError(f"unknown regime {regime!r}")
    _validate_pools()
    h = _open_root(Path(out_root))
    rng = random.Random(f"e03:{regime}:{seed}")
    if regime == "healthy":
        meta = _healthy_like(h, rng, basin=False)
    elif regime == "soft_basin":
        meta = _healthy_like(h, rng, basin=True)
    elif regime == "hard_circling":
        meta = _hard_circling(h, rng)
    elif regime == "wrong_but_stable":
        meta = _wrong_family(h, seed, mimic=False)
    else:
        meta = _wrong_family(h, seed, mimic=True)
    meta.update({
        "regime": regime,
        "seed": seed,
        "root": str(out_root),
        "events": h._next_seq,
        "artifacts": len(h.state.artifacts),
    })
    return meta

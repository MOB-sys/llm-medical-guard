"""Check for known drug-drug and drug-supplement interactions."""

from __future__ import annotations

from llm_medical_guard.checks import BaseCheck, CheckRegistry
from llm_medical_guard.config import GuardConfig
from llm_medical_guard.result import CheckResult, CheckStatus, Severity

# Well-documented dangerous interactions (evidence-based, publicly available)
# Source: FDA drug labels, DailyMed, established medical literature
_KNOWN_INTERACTIONS: list[dict] = [
    # Blood thinners + NSAIDs
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": [
            "aspirin", "ibuprofen", "naproxen",
            "advil", "motrin", "aleve", "nsaid",
        ],
        "severity": "danger",
        "description": (
            "Increased risk of serious bleeding."
            " NSAIDs inhibit platelet function and may"
            " displace warfarin from protein binding."
        ),
        "source": "FDA Drug Label",
    },
    # ACE inhibitors + Potassium
    {
        "drug_a": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "drug_b": ["potassium", "potassium chloride", "potassium supplement"],
        "severity": "warning",
        "description": "Risk of hyperkalemia (dangerously high potassium levels).",
        "source": "FDA Drug Label",
    },
    # SSRIs + MAOIs
    {
        "drug_a": [
            "fluoxetine", "sertraline", "paroxetine",
            "citalopram", "escitalopram", "ssri",
        ],
        "drug_b": [
            "phenelzine", "tranylcypromine",
            "isocarboxazid", "selegiline", "maoi",
        ],
        "severity": "danger",
        "description": (
            "Risk of serotonin syndrome,"
            " a potentially life-threatening condition."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # Statins + Grapefruit
    {
        "drug_a": ["atorvastatin", "simvastatin", "lovastatin", "statin"],
        "drug_b": ["grapefruit", "grapefruit juice"],
        "severity": "warning",
        "description": (
            "Grapefruit inhibits CYP3A4 enzyme,"
            " increasing statin blood levels and risk"
            " of muscle damage (rhabdomyolysis)."
        ),
        "source": "FDA Consumer Update",
    },
    # Metformin + Alcohol
    {
        "drug_a": ["metformin", "glucophage"],
        "drug_b": ["alcohol", "ethanol"],
        "severity": "warning",
        "description": (
            "Increased risk of lactic acidosis,"
            " especially with heavy alcohol use."
        ),
        "source": "FDA Drug Label",
    },
    # Blood thinners + Vitamin K
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": ["vitamin k", "phytonadione"],
        "severity": "warning",
        "description": (
            "Vitamin K counteracts warfarin's"
            " anticoagulant effect, potentially"
            " leading to blood clots."
        ),
        "source": "NIH Office of Dietary Supplements",
    },
    # Blood thinners + Fish oil
    {
        "drug_a": [
            "warfarin", "coumadin", "aspirin",
            "clopidogrel", "plavix",
        ],
        "drug_b": [
            "fish oil", "omega-3", "omega 3",
            "epa", "dha",
        ],
        "severity": "caution",
        "description": (
            "May increase bleeding risk due to"
            " additive antiplatelet effects."
        ),
        "source": "NIH / Natural Medicines Database",
    },
    # Thyroid medication + Calcium/Iron
    {
        "drug_a": [
            "levothyroxine", "synthroid",
            "thyroid medication",
        ],
        "drug_b": [
            "calcium", "iron",
            "calcium carbonate", "ferrous sulfate",
        ],
        "severity": "warning",
        "description": (
            "Calcium and iron reduce absorption of"
            " thyroid medication."
            " Take at least 4 hours apart."
        ),
        "source": "American Thyroid Association",
    },
    # Antibiotics + Dairy
    {
        "drug_a": [
            "tetracycline", "doxycycline",
            "ciprofloxacin", "levofloxacin",
        ],
        "drug_b": ["calcium", "dairy", "milk", "antacid"],
        "severity": "warning",
        "description": (
            "Calcium-containing products reduce"
            " antibiotic absorption significantly."
        ),
        "source": "FDA Drug Label",
    },
    # St. John's Wort interactions
    {
        "drug_a": [
            "st. john's wort",
            "st john's wort", "hypericum",
        ],
        "drug_b": [
            "birth control", "oral contraceptive",
            "contraceptive", "ssri", "fluoxetine",
            "sertraline", "warfarin",
            "cyclosporine", "digoxin",
        ],
        "severity": "danger",
        "description": (
            "St. John's Wort induces CYP450 enzymes,"
            " reducing effectiveness of many"
            " medications."
        ),
        "source": "NIH NCCIH",
    },
    # Calcium + Iron (absorption competition)
    {
        "drug_a": ["calcium", "calcium carbonate", "calcium citrate"],
        "drug_b": ["iron", "ferrous sulfate", "ferrous gluconate"],
        "severity": "caution",
        "description": (
            "Calcium inhibits iron absorption."
            " Take at different times of day."
        ),
        "source": "NIH Office of Dietary Supplements",
    },
    # Vitamin E + Blood thinners
    {
        "drug_a": ["vitamin e", "tocopherol"],
        "drug_b": ["warfarin", "aspirin", "clopidogrel", "blood thinner"],
        "severity": "caution",
        "description": (
            "High-dose Vitamin E may increase"
            " bleeding risk with anticoagulants."
        ),
        "source": "NIH Office of Dietary Supplements",
    },
    # Ginkgo + Blood thinners
    {
        "drug_a": ["ginkgo", "ginkgo biloba"],
        "drug_b": [
            "warfarin", "aspirin", "ibuprofen",
            "blood thinner", "anticoagulant",
        ],
        "severity": "warning",
        "description": (
            "Ginkgo has antiplatelet properties"
            " and may increase bleeding risk."
        ),
        "source": "NCCIH / Natural Medicines Database",
    },
    # Magnesium + Antibiotics
    {
        "drug_a": [
            "magnesium", "magnesium oxide",
            "magnesium citrate",
        ],
        "drug_b": [
            "tetracycline", "doxycycline",
            "ciprofloxacin", "levofloxacin",
        ],
        "severity": "warning",
        "description": (
            "Magnesium reduces absorption of certain"
            " antibiotics. Separate by 2-4 hours."
        ),
        "source": "FDA Drug Label",
    },
    # Zinc + Copper
    {
        "drug_a": ["zinc"],
        "drug_b": ["copper"],
        "severity": "caution",
        "description": (
            "High-dose zinc can cause copper"
            " deficiency over time."
        ),
        "source": "NIH Office of Dietary Supplements",
    },
    # --- Cardiovascular drugs ---
    # Warfarin + Amiodarone
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": ["amiodarone", "cordarone", "pacerone"],
        "severity": "danger",
        "description": (
            "Amiodarone inhibits warfarin metabolism via CYP2C9,"
            " significantly increasing INR and bleeding risk."
            " Warfarin dose reduction of 30-50% typically required."
        ),
        "source": "FDA Drug Label",
    },
    # Simvastatin + Amiodarone
    {
        "drug_a": ["simvastatin", "zocor"],
        "drug_b": ["amiodarone", "cordarone"],
        "severity": "danger",
        "description": (
            "Amiodarone inhibits CYP3A4, raising simvastatin levels"
            " and increasing risk of rhabdomyolysis."
            " Simvastatin dose should not exceed 20mg."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # ACE inhibitors + ARBs (dual RAAS blockade)
    {
        "drug_a": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "drug_b": [
            "losartan", "valsartan", "irbesartan",
            "candesartan", "olmesartan", "arb",
        ],
        "severity": "danger",
        "description": (
            "Dual RAAS blockade increases risk of hyperkalemia,"
            " hypotension, and renal impairment."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # ACE inhibitors + Spironolactone
    {
        "drug_a": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "drug_b": ["spironolactone", "aldactone", "eplerenone", "inspra"],
        "severity": "warning",
        "description": (
            "Combined use increases risk of hyperkalemia."
            " Monitor potassium levels closely."
        ),
        "source": "FDA Drug Label",
    },
    # Beta-blockers + Verapamil/Diltiazem
    {
        "drug_a": [
            "metoprolol", "atenolol", "propranolol",
            "carvedilol", "beta blocker",
        ],
        "drug_b": ["verapamil", "calan", "diltiazem", "cardizem"],
        "severity": "danger",
        "description": (
            "Combined use may cause severe bradycardia,"
            " heart block, or cardiac arrest."
        ),
        "source": "FDA Drug Label",
    },
    # Digoxin + Amiodarone
    {
        "drug_a": ["digoxin", "lanoxin"],
        "drug_b": ["amiodarone", "cordarone"],
        "severity": "danger",
        "description": (
            "Amiodarone increases digoxin levels by ~70%."
            " Risk of digoxin toxicity with fatal arrhythmias."
            " Reduce digoxin dose by 50%."
        ),
        "source": "FDA Drug Label",
    },
    # Digoxin + Verapamil
    {
        "drug_a": ["digoxin", "lanoxin"],
        "drug_b": ["verapamil", "calan"],
        "severity": "warning",
        "description": (
            "Verapamil increases digoxin serum levels"
            " and risk of toxicity. Monitor digoxin levels."
        ),
        "source": "FDA Drug Label",
    },
    # Clopidogrel + Omeprazole
    {
        "drug_a": ["clopidogrel", "plavix"],
        "drug_b": ["omeprazole", "prilosec"],
        "severity": "warning",
        "description": (
            "Omeprazole inhibits CYP2C19, reducing conversion"
            " of clopidogrel to its active metabolite."
            " Use pantoprazole instead if PPI needed."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # Warfarin + Metronidazole
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": ["metronidazole", "flagyl"],
        "severity": "danger",
        "description": (
            "Metronidazole inhibits warfarin metabolism,"
            " significantly increasing INR and bleeding risk."
        ),
        "source": "FDA Drug Label",
    },
    # Warfarin + Fluconazole
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": ["fluconazole", "diflucan"],
        "severity": "danger",
        "description": (
            "Fluconazole is a potent CYP2C9 inhibitor,"
            " markedly increasing warfarin levels and bleeding risk."
        ),
        "source": "FDA Drug Label",
    },
    # Statin + Fibrate
    {
        "drug_a": [
            "atorvastatin", "simvastatin", "rosuvastatin",
            "lovastatin", "pravastatin", "statin",
        ],
        "drug_b": ["gemfibrozil", "lopid", "fenofibrate", "tricor"],
        "severity": "warning",
        "description": (
            "Combined use increases risk of myopathy"
            " and rhabdomyolysis. Gemfibrozil poses"
            " greater risk than fenofibrate."
        ),
        "source": "FDA Drug Label",
    },
    # Statin + Clarithromycin/Erythromycin
    {
        "drug_a": ["atorvastatin", "simvastatin", "lovastatin", "statin"],
        "drug_b": [
            "clarithromycin", "biaxin",
            "erythromycin", "ery-tab",
        ],
        "severity": "danger",
        "description": (
            "Macrolide antibiotics inhibit CYP3A4,"
            " significantly increasing statin levels"
            " and risk of rhabdomyolysis."
        ),
        "source": "FDA Drug Label",
    },
    # Amlodipine + Simvastatin
    {
        "drug_a": ["amlodipine", "norvasc"],
        "drug_b": ["simvastatin", "zocor"],
        "severity": "warning",
        "description": (
            "Amlodipine increases simvastatin exposure."
            " Simvastatin dose should not exceed 20mg"
            " when used with amlodipine."
        ),
        "source": "FDA Drug Label",
    },
    # Potassium-sparing diuretics + Potassium
    {
        "drug_a": [
            "spironolactone", "aldactone",
            "triamterene", "amiloride",
        ],
        "drug_b": ["potassium", "potassium chloride", "potassium supplement"],
        "severity": "danger",
        "description": (
            "Combined use can cause life-threatening"
            " hyperkalemia. Avoid concurrent use."
        ),
        "source": "FDA Drug Label",
    },
    # Nitrates + PDE5 inhibitors
    {
        "drug_a": [
            "nitroglycerin", "isosorbide mononitrate",
            "isosorbide dinitrate", "nitrate",
        ],
        "drug_b": [
            "sildenafil", "viagra", "tadalafil",
            "cialis", "vardenafil", "levitra",
        ],
        "severity": "danger",
        "description": (
            "Combined use can cause severe, potentially fatal"
            " hypotension. Absolutely contraindicated."
        ),
        "source": "FDA Drug Label",
    },
    # Warfarin + Cranberry
    {
        "drug_a": ["warfarin", "coumadin"],
        "drug_b": ["cranberry", "cranberry juice", "cranberry extract"],
        "severity": "caution",
        "description": (
            "Cranberry may increase warfarin effect"
            " and INR. Monitor INR if consuming"
            " large quantities."
        ),
        "source": "MHRA Drug Safety Update",
    },
    # --- CNS drugs ---
    # SSRIs + Tramadol
    {
        "drug_a": [
            "fluoxetine", "sertraline", "paroxetine",
            "citalopram", "escitalopram", "ssri",
        ],
        "drug_b": ["tramadol", "ultram"],
        "severity": "danger",
        "description": (
            "Combined serotonergic activity increases"
            " risk of serotonin syndrome and seizures."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # SSRIs + Triptans
    {
        "drug_a": [
            "fluoxetine", "sertraline", "paroxetine",
            "citalopram", "escitalopram", "ssri",
        ],
        "drug_b": [
            "sumatriptan", "imitrex", "rizatriptan",
            "maxalt", "zolmitriptan", "triptan",
        ],
        "severity": "warning",
        "description": (
            "Combined use may increase risk of"
            " serotonin syndrome. Monitor for symptoms."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # SSRIs + NSAIDs
    {
        "drug_a": [
            "fluoxetine", "sertraline", "paroxetine",
            "citalopram", "escitalopram", "ssri",
        ],
        "drug_b": [
            "ibuprofen", "naproxen", "aspirin",
            "advil", "motrin", "aleve", "nsaid",
        ],
        "severity": "warning",
        "description": (
            "SSRIs impair platelet function; combined"
            " with NSAIDs, GI bleeding risk increases"
            " substantially."
        ),
        "source": "BMJ Clinical Evidence",
    },
    # Benzodiazepines + Opioids
    {
        "drug_a": [
            "diazepam", "valium", "alprazolam", "xanax",
            "lorazepam", "ativan", "clonazepam",
            "klonopin", "benzodiazepine",
        ],
        "drug_b": [
            "oxycodone", "oxycontin", "hydrocodone",
            "vicodin", "morphine", "fentanyl",
            "codeine", "tramadol", "opioid",
        ],
        "severity": "danger",
        "description": (
            "Combined CNS depression can cause profound"
            " sedation, respiratory depression, coma,"
            " and death."
        ),
        "source": "FDA Boxed Warning",
    },
    # Opioids + Alcohol
    {
        "drug_a": [
            "oxycodone", "oxycontin", "hydrocodone",
            "vicodin", "morphine", "fentanyl",
            "codeine", "tramadol", "opioid",
        ],
        "drug_b": ["alcohol", "ethanol"],
        "severity": "danger",
        "description": (
            "Alcohol potentiates opioid-induced respiratory"
            " depression. Can be fatal."
        ),
        "source": "FDA Boxed Warning",
    },
    # Benzodiazepines + Alcohol
    {
        "drug_a": [
            "diazepam", "valium", "alprazolam", "xanax",
            "lorazepam", "ativan", "clonazepam",
            "klonopin", "benzodiazepine",
        ],
        "drug_b": ["alcohol", "ethanol"],
        "severity": "danger",
        "description": (
            "Additive CNS depression can cause excessive"
            " sedation, respiratory depression, and death."
        ),
        "source": "FDA Drug Label",
    },
    # Carbamazepine + Oral contraceptives
    {
        "drug_a": ["carbamazepine", "tegretol"],
        "drug_b": [
            "birth control", "oral contraceptive",
            "contraceptive", "ethinyl estradiol",
        ],
        "severity": "danger",
        "description": (
            "Carbamazepine induces CYP3A4, reducing"
            " contraceptive hormone levels and efficacy."
            " Use alternative contraception."
        ),
        "source": "FDA Drug Label",
    },
    # Carbamazepine + Valproic acid
    {
        "drug_a": ["carbamazepine", "tegretol"],
        "drug_b": ["valproic acid", "depakote", "divalproex", "valproate"],
        "severity": "warning",
        "description": (
            "Carbamazepine lowers valproate levels;"
            " valproate increases carbamazepine epoxide"
            " (toxic metabolite). Monitor levels."
        ),
        "source": "FDA Drug Label",
    },
    # Phenytoin + Valproic acid
    {
        "drug_a": ["phenytoin", "dilantin"],
        "drug_b": ["valproic acid", "depakote", "divalproex", "valproate"],
        "severity": "warning",
        "description": (
            "Complex interaction: valproate displaces"
            " phenytoin from protein binding and"
            " inhibits its metabolism. Monitor levels."
        ),
        "source": "FDA Drug Label",
    },
    # Lithium + NSAIDs
    {
        "drug_a": ["lithium", "lithobid", "eskalith"],
        "drug_b": [
            "ibuprofen", "naproxen", "advil",
            "motrin", "aleve", "nsaid", "indomethacin",
        ],
        "severity": "danger",
        "description": (
            "NSAIDs reduce renal lithium clearance,"
            " causing lithium toxicity."
            " Use with extreme caution."
        ),
        "source": "FDA Drug Label",
    },
    # Lithium + ACE inhibitors
    {
        "drug_a": ["lithium", "lithobid"],
        "drug_b": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "severity": "warning",
        "description": (
            "ACE inhibitors reduce renal lithium clearance,"
            " increasing lithium levels and toxicity risk."
        ),
        "source": "FDA Drug Label",
    },
    # Lithium + Diuretics (thiazide)
    {
        "drug_a": ["lithium", "lithobid"],
        "drug_b": [
            "hydrochlorothiazide", "hctz",
            "chlorthalidone", "thiazide",
        ],
        "severity": "danger",
        "description": (
            "Thiazide diuretics reduce lithium clearance"
            " by 25-40%, causing lithium toxicity."
        ),
        "source": "FDA Drug Label",
    },
    # Antipsychotics + QT-prolonging agents
    {
        "drug_a": [
            "haloperidol", "haldol", "ziprasidone",
            "geodon", "thioridazine",
        ],
        "drug_b": [
            "erythromycin", "clarithromycin",
            "moxifloxacin", "avelox", "sotalol",
            "amiodarone", "methadone",
        ],
        "severity": "danger",
        "description": (
            "Additive QT prolongation increases risk of"
            " Torsades de Pointes and sudden cardiac death."
        ),
        "source": "CredibleMeds / FDA Drug Label",
    },
    # Fluoxetine + Tamoxifen
    {
        "drug_a": ["fluoxetine", "prozac", "paroxetine", "paxil"],
        "drug_b": ["tamoxifen", "nolvadex"],
        "severity": "danger",
        "description": (
            "Strong CYP2D6 inhibition by fluoxetine/paroxetine"
            " blocks conversion of tamoxifen to active metabolite"
            " endoxifen, reducing cancer treatment efficacy."
        ),
        "source": "FDA Drug Label / NCCN Guidelines",
    },
    # Trazodone + SSRIs
    {
        "drug_a": ["trazodone", "desyrel"],
        "drug_b": [
            "fluoxetine", "sertraline", "paroxetine",
            "citalopram", "escitalopram", "ssri",
        ],
        "severity": "warning",
        "description": (
            "Combined serotonergic activity increases"
            " risk of serotonin syndrome."
        ),
        "source": "FDA Drug Label",
    },
    # --- Antibiotics / Antifungals ---
    # Fluoroquinolones + QT-prolonging drugs
    {
        "drug_a": [
            "ciprofloxacin", "levofloxacin",
            "moxifloxacin", "avelox",
        ],
        "drug_b": [
            "sotalol", "amiodarone", "haloperidol",
            "methadone", "ondansetron", "zofran",
        ],
        "severity": "danger",
        "description": (
            "Fluoroquinolones prolong QT interval."
            " Combined with other QT-prolonging drugs,"
            " risk of fatal arrhythmia increases."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # Fluoroquinolones + Theophylline
    {
        "drug_a": ["ciprofloxacin", "cipro"],
        "drug_b": ["theophylline", "aminophylline"],
        "severity": "warning",
        "description": (
            "Ciprofloxacin inhibits CYP1A2, increasing"
            " theophylline levels and risk of seizures"
            " and arrhythmias."
        ),
        "source": "FDA Drug Label",
    },
    # Fluoroquinolones + Corticosteroids
    {
        "drug_a": [
            "ciprofloxacin", "levofloxacin",
            "moxifloxacin", "fluoroquinolone",
        ],
        "drug_b": [
            "prednisone", "dexamethasone",
            "methylprednisolone", "corticosteroid",
        ],
        "severity": "warning",
        "description": (
            "Combined use increases risk of tendon"
            " rupture, especially in older adults."
        ),
        "source": "FDA Boxed Warning",
    },
    # Ketoconazole + Statins
    {
        "drug_a": ["ketoconazole", "nizoral", "itraconazole", "sporanox"],
        "drug_b": ["simvastatin", "lovastatin", "atorvastatin", "statin"],
        "severity": "danger",
        "description": (
            "Azole antifungals are potent CYP3A4 inhibitors,"
            " dramatically increasing statin levels"
            " and risk of rhabdomyolysis."
        ),
        "source": "FDA Drug Label",
    },
    # Fluconazole + Citalopram/Escitalopram
    {
        "drug_a": ["fluconazole", "diflucan"],
        "drug_b": ["citalopram", "celexa", "escitalopram", "lexapro"],
        "severity": "warning",
        "description": (
            "Fluconazole inhibits CYP2C19/3A4, increasing"
            " citalopram levels and QT prolongation risk."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # Macrolides + Digoxin
    {
        "drug_a": [
            "clarithromycin", "biaxin",
            "erythromycin", "azithromycin", "zithromax",
        ],
        "drug_b": ["digoxin", "lanoxin"],
        "severity": "warning",
        "description": (
            "Macrolides increase digoxin absorption"
            " by eliminating gut bacteria that metabolize it."
            " Monitor digoxin levels."
        ),
        "source": "FDA Drug Label",
    },
    # Metronidazole + Alcohol
    {
        "drug_a": ["metronidazole", "flagyl"],
        "drug_b": ["alcohol", "ethanol"],
        "severity": "danger",
        "description": (
            "Disulfiram-like reaction: severe nausea,"
            " vomiting, flushing, and headache."
            " Avoid alcohol during and 3 days after."
        ),
        "source": "FDA Drug Label",
    },
    # Trimethoprim + ACE inhibitors
    {
        "drug_a": [
            "trimethoprim", "bactrim",
            "sulfamethoxazole-trimethoprim", "tmp-smx",
        ],
        "drug_b": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "severity": "warning",
        "description": (
            "Trimethoprim blocks renal potassium excretion."
            " Combined with ACE inhibitors, risk of"
            " life-threatening hyperkalemia."
        ),
        "source": "BMJ / FDA Drug Label",
    },
    # Rifampin + many drugs
    {
        "drug_a": ["rifampin", "rifadin", "rifampicin"],
        "drug_b": [
            "warfarin", "oral contraceptive", "birth control",
            "cyclosporine", "tacrolimus", "methadone",
        ],
        "severity": "danger",
        "description": (
            "Rifampin is one of the most potent CYP450"
            " inducers. Dramatically reduces levels of many"
            " drugs, potentially causing treatment failure."
        ),
        "source": "FDA Drug Label",
    },
    # Linezolid + Serotonergic drugs
    {
        "drug_a": ["linezolid", "zyvox"],
        "drug_b": [
            "fluoxetine", "sertraline", "ssri",
            "venlafaxine", "duloxetine", "snri",
            "meperidine", "demerol",
        ],
        "severity": "danger",
        "description": (
            "Linezolid is a reversible MAO inhibitor."
            " Combined with serotonergic drugs, risk of"
            " serotonin syndrome."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # --- Diabetes drugs ---
    # Metformin + Contrast dye
    {
        "drug_a": ["metformin", "glucophage"],
        "drug_b": ["contrast dye", "iodinated contrast", "contrast media"],
        "severity": "warning",
        "description": (
            "Risk of contrast-induced nephropathy leading"
            " to metformin accumulation and lactic acidosis."
            " Hold metformin 48 hours around contrast."
        ),
        "source": "ACR / FDA Drug Label",
    },
    # Sulfonylureas + Fluconazole
    {
        "drug_a": [
            "glipizide", "glucotrol", "glyburide",
            "glibenclamide", "glimepiride", "amaryl",
            "sulfonylurea",
        ],
        "drug_b": ["fluconazole", "diflucan"],
        "severity": "warning",
        "description": (
            "Fluconazole inhibits CYP2C9, increasing"
            " sulfonylurea levels and risk of severe"
            " hypoglycemia."
        ),
        "source": "FDA Drug Label",
    },
    # Sulfonylureas + Beta-blockers
    {
        "drug_a": [
            "glipizide", "glyburide", "glimepiride",
            "sulfonylurea",
        ],
        "drug_b": [
            "metoprolol", "atenolol", "propranolol",
            "beta blocker",
        ],
        "severity": "caution",
        "description": (
            "Beta-blockers may mask symptoms of"
            " hypoglycemia (tachycardia, tremor)"
            " and impair glucose recovery."
        ),
        "source": "FDA Drug Label",
    },
    # Insulin + ACE inhibitors
    {
        "drug_a": ["insulin", "insulin glargine", "lantus", "humalog"],
        "drug_b": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "severity": "caution",
        "description": (
            "ACE inhibitors may increase insulin"
            " sensitivity, raising hypoglycemia risk."
            " Monitor blood glucose."
        ),
        "source": "FDA Drug Label",
    },
    # Metformin + Topiramate
    {
        "drug_a": ["metformin", "glucophage"],
        "drug_b": ["topiramate", "topamax"],
        "severity": "warning",
        "description": (
            "Topiramate may cause metabolic acidosis,"
            " increasing risk of lactic acidosis"
            " when combined with metformin."
        ),
        "source": "FDA Drug Label",
    },
    # --- Common supplements ---
    # CoQ10 + Warfarin
    {
        "drug_a": ["coq10", "coenzyme q10", "ubiquinone", "ubiquinol"],
        "drug_b": ["warfarin", "coumadin"],
        "severity": "warning",
        "description": (
            "CoQ10 is structurally similar to vitamin K"
            " and may reduce warfarin anticoagulant effect."
        ),
        "source": "Natural Medicines Database",
    },
    # Turmeric/Curcumin + Anticoagulants
    {
        "drug_a": ["turmeric", "curcumin"],
        "drug_b": [
            "warfarin", "coumadin", "aspirin",
            "clopidogrel", "plavix", "blood thinner",
        ],
        "severity": "warning",
        "description": (
            "Curcumin has antiplatelet properties and"
            " may inhibit CYP enzymes, increasing"
            " bleeding risk with anticoagulants."
        ),
        "source": "NIH NCCIH / Natural Medicines Database",
    },
    # Green tea extract + Warfarin
    {
        "drug_a": ["green tea extract", "green tea", "egcg"],
        "drug_b": ["warfarin", "coumadin"],
        "severity": "caution",
        "description": (
            "Green tea contains vitamin K which may"
            " reduce warfarin efficacy. High-dose"
            " extracts may have greater effect."
        ),
        "source": "NIH NCCIH",
    },
    # Green tea extract + Nadolol
    {
        "drug_a": ["green tea extract", "green tea", "egcg"],
        "drug_b": ["nadolol", "corgard"],
        "severity": "caution",
        "description": (
            "Green tea may reduce nadolol absorption"
            " by up to 85% via OATP inhibition,"
            " reducing its blood pressure lowering effect."
        ),
        "source": "Clinical Pharmacology & Therapeutics",
    },
    # Garlic supplements + Anticoagulants
    {
        "drug_a": ["garlic supplement", "garlic extract", "allicin"],
        "drug_b": [
            "warfarin", "coumadin", "aspirin",
            "clopidogrel", "blood thinner",
        ],
        "severity": "caution",
        "description": (
            "Garlic supplements have antiplatelet"
            " properties and may increase bleeding risk."
        ),
        "source": "NIH NCCIH",
    },
    # Garlic + Saquinavir
    {
        "drug_a": ["garlic supplement", "garlic extract", "allicin"],
        "drug_b": ["saquinavir", "invirase"],
        "severity": "warning",
        "description": (
            "Garlic supplements can reduce saquinavir"
            " blood levels by ~50%, potentially causing"
            " HIV treatment failure."
        ),
        "source": "NIH NCCIH / Clin Infect Dis",
    },
    # Ginseng + Warfarin
    {
        "drug_a": ["ginseng", "panax ginseng", "korean ginseng"],
        "drug_b": ["warfarin", "coumadin"],
        "severity": "caution",
        "description": (
            "Ginseng may reduce warfarin effectiveness"
            " by increasing warfarin metabolism."
            " Monitor INR."
        ),
        "source": "NIH NCCIH",
    },
    # Ginseng + Diabetes medications
    {
        "drug_a": ["ginseng", "panax ginseng", "korean ginseng"],
        "drug_b": [
            "insulin", "metformin", "glipizide",
            "glyburide", "diabetes medication",
        ],
        "severity": "caution",
        "description": (
            "Ginseng may lower blood glucose levels,"
            " increasing risk of hypoglycemia when"
            " combined with diabetes medications."
        ),
        "source": "NIH NCCIH",
    },
    # Melatonin + Sedatives
    {
        "drug_a": ["melatonin"],
        "drug_b": [
            "zolpidem", "ambien", "diazepam",
            "lorazepam", "alprazolam", "benzodiazepine",
        ],
        "severity": "caution",
        "description": (
            "Additive sedation may cause excessive"
            " drowsiness and impaired coordination."
        ),
        "source": "Natural Medicines Database",
    },
    # Melatonin + Anticoagulants
    {
        "drug_a": ["melatonin"],
        "drug_b": ["warfarin", "coumadin"],
        "severity": "caution",
        "description": (
            "Melatonin may increase anticoagulant effect"
            " of warfarin. Monitor INR."
        ),
        "source": "Natural Medicines Database",
    },
    # Kava + Hepatotoxic drugs
    {
        "drug_a": ["kava", "kava kava"],
        "drug_b": [
            "acetaminophen", "tylenol",
            "statin", "atorvastatin",
        ],
        "severity": "warning",
        "description": (
            "Kava is hepatotoxic. Combined with other"
            " hepatotoxic drugs, risk of liver damage"
            " is increased."
        ),
        "source": "FDA Consumer Advisory / NIH NCCIH",
    },
    # --- GI drugs ---
    # PPIs + Clopidogrel (already have omeprazole, adding others)
    {
        "drug_a": ["esomeprazole", "nexium"],
        "drug_b": ["clopidogrel", "plavix"],
        "severity": "warning",
        "description": (
            "Esomeprazole inhibits CYP2C19, reducing"
            " clopidogrel activation. Consider"
            " pantoprazole as alternative."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # PPIs + Methotrexate
    {
        "drug_a": [
            "omeprazole", "prilosec", "esomeprazole",
            "nexium", "lansoprazole", "prevacid", "ppi",
        ],
        "drug_b": ["methotrexate", "trexall"],
        "severity": "warning",
        "description": (
            "PPIs may decrease renal clearance of"
            " methotrexate, increasing toxicity risk,"
            " especially at high doses."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # PPIs + Iron
    {
        "drug_a": [
            "omeprazole", "prilosec", "esomeprazole",
            "nexium", "lansoprazole", "prevacid", "ppi",
        ],
        "drug_b": ["iron", "ferrous sulfate", "ferrous gluconate"],
        "severity": "caution",
        "description": (
            "PPIs reduce stomach acid, decreasing"
            " iron absorption. Take iron separately"
            " or consider IV iron if deficient."
        ),
        "source": "Am J Hematol / FDA Drug Label",
    },
    # PPIs + Calcium
    {
        "drug_a": [
            "omeprazole", "prilosec", "esomeprazole",
            "nexium", "lansoprazole", "prevacid", "ppi",
        ],
        "drug_b": ["calcium carbonate", "calcium"],
        "severity": "caution",
        "description": (
            "Long-term PPI use reduces calcium absorption,"
            " increasing fracture risk. Use calcium citrate"
            " (does not require acid for absorption)."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # PPIs + Vitamin B12
    {
        "drug_a": [
            "omeprazole", "prilosec", "esomeprazole",
            "nexium", "lansoprazole", "prevacid", "ppi",
        ],
        "drug_b": ["vitamin b12", "cyanocobalamin", "b12"],
        "severity": "caution",
        "description": (
            "Long-term PPI use reduces vitamin B12"
            " absorption. Monitor B12 levels with"
            " prolonged therapy."
        ),
        "source": "JAMA / FDA Drug Label",
    },
    # PPIs + Magnesium
    {
        "drug_a": [
            "omeprazole", "esomeprazole",
            "lansoprazole", "ppi",
        ],
        "drug_b": ["magnesium", "magnesium level"],
        "severity": "caution",
        "description": (
            "Long-term PPI use (>1 year) may cause"
            " hypomagnesemia. Monitor magnesium levels."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # H2 blockers + Ketoconazole
    {
        "drug_a": [
            "ranitidine", "famotidine", "pepcid",
            "cimetidine", "tagamet", "h2 blocker",
        ],
        "drug_b": ["ketoconazole", "nizoral", "itraconazole", "sporanox"],
        "severity": "warning",
        "description": (
            "Reduced stomach acid decreases azole"
            " antifungal absorption, potentially"
            " causing treatment failure."
        ),
        "source": "FDA Drug Label",
    },
    # Cimetidine + Warfarin
    {
        "drug_a": ["cimetidine", "tagamet"],
        "drug_b": ["warfarin", "coumadin"],
        "severity": "warning",
        "description": (
            "Cimetidine inhibits CYP1A2/2C19/3A4,"
            " increasing warfarin levels and bleeding risk."
        ),
        "source": "FDA Drug Label",
    },
    # --- Pain medications ---
    # Acetaminophen + Alcohol
    {
        "drug_a": ["acetaminophen", "tylenol", "paracetamol"],
        "drug_b": ["alcohol", "ethanol"],
        "severity": "danger",
        "description": (
            "Alcohol induces CYP2E1, increasing formation of"
            " hepatotoxic NAPQI metabolite. Risk of severe"
            " liver damage, especially with chronic alcohol use."
        ),
        "source": "FDA Boxed Warning",
    },
    # NSAIDs + ACE inhibitors
    {
        "drug_a": [
            "ibuprofen", "naproxen", "advil",
            "motrin", "aleve", "nsaid",
            "diclofenac", "indomethacin", "celecoxib",
        ],
        "drug_b": ["lisinopril", "enalapril", "ramipril", "ace inhibitor"],
        "severity": "warning",
        "description": (
            "NSAIDs reduce antihypertensive effect of"
            " ACE inhibitors and increase risk of"
            " acute kidney injury, especially in"
            " dehydrated patients."
        ),
        "source": "FDA Drug Label",
    },
    # NSAIDs + Lithium
    # (already listed above under lithium, adding reverse reference)
    # NSAIDs + SSRIs (already listed above)
    # NSAIDs + Methotrexate
    {
        "drug_a": [
            "ibuprofen", "naproxen", "advil",
            "motrin", "aleve", "nsaid",
            "diclofenac", "indomethacin",
        ],
        "drug_b": ["methotrexate", "trexall"],
        "severity": "danger",
        "description": (
            "NSAIDs decrease renal clearance of methotrexate,"
            " causing potentially fatal toxicity."
        ),
        "source": "FDA Drug Label",
    },
    # NSAIDs + Diuretics
    {
        "drug_a": [
            "ibuprofen", "naproxen", "nsaid",
            "diclofenac", "celecoxib",
        ],
        "drug_b": [
            "furosemide", "lasix",
            "hydrochlorothiazide", "hctz", "diuretic",
        ],
        "severity": "caution",
        "description": (
            "NSAIDs reduce diuretic efficacy and may"
            " increase risk of acute kidney injury."
        ),
        "source": "FDA Drug Label",
    },
    # Acetaminophen + Warfarin
    {
        "drug_a": ["acetaminophen", "tylenol", "paracetamol"],
        "drug_b": ["warfarin", "coumadin"],
        "severity": "caution",
        "description": (
            "Regular acetaminophen use (>2g/day) may"
            " increase INR and bleeding risk."
            " Monitor INR with chronic use."
        ),
        "source": "FDA Drug Label / Ann Pharmacother",
    },
    # Opioids + Gabapentin/Pregabalin
    {
        "drug_a": [
            "oxycodone", "hydrocodone", "morphine",
            "fentanyl", "codeine", "opioid",
        ],
        "drug_b": [
            "gabapentin", "neurontin",
            "pregabalin", "lyrica",
        ],
        "severity": "warning",
        "description": (
            "Additive CNS and respiratory depression."
            " Increased risk of overdose death."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # --- Thyroid medications ---
    # Levothyroxine + Soy
    {
        "drug_a": ["levothyroxine", "synthroid", "thyroid medication"],
        "drug_b": ["soy", "soy protein", "soy isoflavones"],
        "severity": "caution",
        "description": (
            "Soy products may decrease levothyroxine"
            " absorption. Separate by at least 4 hours."
        ),
        "source": "Thyroid / FDA Drug Label",
    },
    # Levothyroxine + PPIs
    {
        "drug_a": ["levothyroxine", "synthroid", "thyroid medication"],
        "drug_b": [
            "omeprazole", "prilosec", "esomeprazole",
            "nexium", "lansoprazole", "ppi",
        ],
        "severity": "caution",
        "description": (
            "PPIs reduce stomach acid needed for"
            " levothyroxine absorption."
            " May require dose increase."
        ),
        "source": "J Clin Endocrinol Metab / FDA Drug Label",
    },
    # Levothyroxine + Cholestyramine
    {
        "drug_a": ["levothyroxine", "synthroid", "thyroid medication"],
        "drug_b": [
            "cholestyramine", "questran",
            "colestipol", "colesevelam", "welchol",
        ],
        "severity": "warning",
        "description": (
            "Bile acid sequestrants bind levothyroxine"
            " in the gut, markedly reducing absorption."
            " Separate by at least 4-6 hours."
        ),
        "source": "FDA Drug Label",
    },
    # Levothyroxine + Coffee
    {
        "drug_a": ["levothyroxine", "synthroid", "thyroid medication"],
        "drug_b": ["coffee", "caffeine", "espresso"],
        "severity": "caution",
        "description": (
            "Coffee can reduce levothyroxine absorption"
            " by ~30%. Take levothyroxine 30-60 minutes"
            " before coffee."
        ),
        "source": "Thyroid / Clinical Endocrinology",
    },
    # Levothyroxine + Sucralfate
    {
        "drug_a": ["levothyroxine", "synthroid"],
        "drug_b": ["sucralfate", "carafate"],
        "severity": "warning",
        "description": (
            "Sucralfate binds levothyroxine, reducing"
            " its absorption. Separate by 8 hours."
        ),
        "source": "FDA Drug Label",
    },
    # Levothyroxine + Aluminum antacids
    {
        "drug_a": ["levothyroxine", "synthroid"],
        "drug_b": [
            "aluminum hydroxide", "maalox",
            "mylanta", "antacid",
        ],
        "severity": "caution",
        "description": (
            "Aluminum-containing antacids reduce"
            " levothyroxine absorption."
            " Separate by at least 4 hours."
        ),
        "source": "FDA Drug Label",
    },
    # --- Immunosuppressants ---
    # Cyclosporine + Ketoconazole
    {
        "drug_a": ["cyclosporine", "sandimmune", "neoral"],
        "drug_b": ["ketoconazole", "nizoral", "itraconazole", "sporanox"],
        "severity": "danger",
        "description": (
            "Azole antifungals inhibit CYP3A4,"
            " dramatically increasing cyclosporine levels"
            " and nephrotoxicity risk."
        ),
        "source": "FDA Drug Label",
    },
    # Cyclosporine + Grapefruit
    {
        "drug_a": ["cyclosporine", "sandimmune", "neoral"],
        "drug_b": ["grapefruit", "grapefruit juice"],
        "severity": "warning",
        "description": (
            "Grapefruit inhibits CYP3A4 and P-gp,"
            " increasing cyclosporine levels."
            " Avoid grapefruit during therapy."
        ),
        "source": "FDA Drug Label",
    },
    # Tacrolimus + Ketoconazole
    {
        "drug_a": ["tacrolimus", "prograf"],
        "drug_b": [
            "ketoconazole", "nizoral",
            "itraconazole", "sporanox",
            "voriconazole", "vfend",
        ],
        "severity": "danger",
        "description": (
            "Azole antifungals significantly increase"
            " tacrolimus levels via CYP3A4 inhibition."
            " Dose reduction and monitoring required."
        ),
        "source": "FDA Drug Label",
    },
    # Tacrolimus + Erythromycin/Clarithromycin
    {
        "drug_a": ["tacrolimus", "prograf"],
        "drug_b": [
            "erythromycin", "clarithromycin", "biaxin",
        ],
        "severity": "danger",
        "description": (
            "Macrolides inhibit CYP3A4, markedly increasing"
            " tacrolimus levels and nephrotoxicity risk."
        ),
        "source": "FDA Drug Label",
    },
    # Cyclosporine + NSAIDs
    {
        "drug_a": ["cyclosporine", "sandimmune", "neoral"],
        "drug_b": [
            "ibuprofen", "naproxen", "diclofenac",
            "nsaid", "indomethacin",
        ],
        "severity": "warning",
        "description": (
            "NSAIDs increase cyclosporine nephrotoxicity."
            " Avoid concurrent use when possible."
        ),
        "source": "FDA Drug Label",
    },
    # Cyclosporine + Potassium-sparing diuretics
    {
        "drug_a": ["cyclosporine", "sandimmune", "neoral"],
        "drug_b": [
            "spironolactone", "aldactone",
            "triamterene", "amiloride",
        ],
        "severity": "warning",
        "description": (
            "Combined use increases hyperkalemia risk."
            " Monitor potassium levels."
        ),
        "source": "FDA Drug Label",
    },
    # Mycophenolate + Antacids/PPIs
    {
        "drug_a": ["mycophenolate", "cellcept", "myfortic"],
        "drug_b": [
            "antacid", "aluminum hydroxide",
            "magnesium hydroxide", "omeprazole", "ppi",
        ],
        "severity": "caution",
        "description": (
            "Antacids and PPIs reduce mycophenolate"
            " absorption. Separate antacids by 2 hours."
        ),
        "source": "FDA Drug Label",
    },
    # --- Antihistamines ---
    # Sedating antihistamines + CNS depressants
    {
        "drug_a": [
            "diphenhydramine", "benadryl",
            "hydroxyzine", "atarax", "vistaril",
            "doxylamine", "chlorpheniramine",
        ],
        "drug_b": [
            "alcohol", "ethanol", "opioid",
            "oxycodone", "hydrocodone",
            "benzodiazepine", "diazepam", "alprazolam",
        ],
        "severity": "warning",
        "description": (
            "Additive CNS depression may cause excessive"
            " sedation, impaired coordination, and"
            " respiratory depression."
        ),
        "source": "FDA Drug Label",
    },
    # Diphenhydramine + Anticholinergics
    {
        "drug_a": ["diphenhydramine", "benadryl"],
        "drug_b": [
            "oxybutynin", "ditropan",
            "tolterodine", "detrol",
            "benztropine", "trihexyphenidyl",
        ],
        "severity": "warning",
        "description": (
            "Additive anticholinergic effects: confusion,"
            " urinary retention, dry mouth, constipation."
            " Especially dangerous in elderly."
        ),
        "source": "Beers Criteria / FDA Drug Label",
    },
    # --- Additional well-documented interactions ---
    # Allopurinol + Azathioprine
    {
        "drug_a": ["allopurinol", "zyloprim"],
        "drug_b": ["azathioprine", "imuran", "mercaptopurine", "6-mp"],
        "severity": "danger",
        "description": (
            "Allopurinol inhibits xanthine oxidase,"
            " blocking azathioprine metabolism."
            " Risk of severe myelosuppression."
            " Reduce azathioprine dose by 75%."
        ),
        "source": "FDA Drug Label",
    },
    # Potassium + Trimethoprim
    {
        "drug_a": ["potassium", "potassium chloride", "potassium supplement"],
        "drug_b": [
            "trimethoprim", "bactrim",
            "sulfamethoxazole-trimethoprim",
        ],
        "severity": "warning",
        "description": (
            "Trimethoprim reduces potassium excretion."
            " Combined with potassium supplements,"
            " risk of hyperkalemia."
        ),
        "source": "BMJ / FDA Drug Label",
    },
    # Sildenafil + Alpha-blockers
    {
        "drug_a": [
            "sildenafil", "viagra", "tadalafil",
            "cialis", "vardenafil",
        ],
        "drug_b": [
            "tamsulosin", "flomax", "doxazosin",
            "cardura", "prazosin", "alpha blocker",
        ],
        "severity": "warning",
        "description": (
            "Combined use may cause symptomatic"
            " orthostatic hypotension."
        ),
        "source": "FDA Drug Label",
    },
    # Ciprofloxacin + Tizanidine
    {
        "drug_a": ["ciprofloxacin", "cipro"],
        "drug_b": ["tizanidine", "zanaflex"],
        "severity": "danger",
        "description": (
            "Ciprofloxacin inhibits CYP1A2, increasing"
            " tizanidine AUC by 10-fold. Risk of"
            " severe hypotension and excessive sedation."
        ),
        "source": "FDA Drug Label",
    },
    # Citalopram + QT-prolonging drugs
    {
        "drug_a": ["citalopram", "celexa"],
        "drug_b": [
            "erythromycin", "moxifloxacin",
            "sotalol", "amiodarone", "methadone",
        ],
        "severity": "danger",
        "description": (
            "Citalopram causes dose-dependent QT"
            " prolongation. Additive QT risk with"
            " other QT-prolonging drugs."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # Valproic acid + Carbapenems
    {
        "drug_a": ["valproic acid", "depakote", "divalproex", "valproate"],
        "drug_b": [
            "meropenem", "ertapenem",
            "imipenem", "doripenem", "carbapenem",
        ],
        "severity": "danger",
        "description": (
            "Carbapenems reduce valproic acid levels by"
            " up to 90% within 24 hours, causing"
            " breakthrough seizures."
        ),
        "source": "FDA Drug Label / Epilepsia",
    },
    # Clonidine + Beta-blockers (withdrawal)
    {
        "drug_a": ["clonidine", "catapres"],
        "drug_b": [
            "metoprolol", "atenolol", "propranolol",
            "beta blocker",
        ],
        "severity": "warning",
        "description": (
            "If clonidine is abruptly discontinued while"
            " on beta-blockers, rebound hypertensive"
            " crisis may occur."
        ),
        "source": "FDA Drug Label",
    },
    # Phenytoin + Oral contraceptives
    {
        "drug_a": ["phenytoin", "dilantin"],
        "drug_b": [
            "birth control", "oral contraceptive",
            "contraceptive", "ethinyl estradiol",
        ],
        "severity": "warning",
        "description": (
            "Phenytoin induces CYP3A4, reducing"
            " oral contraceptive efficacy."
            " Use alternative contraception."
        ),
        "source": "FDA Drug Label",
    },
    # Spironolactone + Digoxin
    {
        "drug_a": ["spironolactone", "aldactone"],
        "drug_b": ["digoxin", "lanoxin"],
        "severity": "caution",
        "description": (
            "Spironolactone may interfere with digoxin"
            " assays and reduce digoxin renal clearance."
            " Monitor digoxin levels."
        ),
        "source": "FDA Drug Label",
    },
    # Duloxetine + Tamoxifen
    {
        "drug_a": ["duloxetine", "cymbalta"],
        "drug_b": ["tamoxifen", "nolvadex"],
        "severity": "warning",
        "description": (
            "Duloxetine moderately inhibits CYP2D6,"
            " reducing tamoxifen activation."
            " Consider alternative antidepressant."
        ),
        "source": "NCCN Guidelines",
    },
    # Venlafaxine + MAOIs
    {
        "drug_a": ["venlafaxine", "effexor", "desvenlafaxine", "pristiq"],
        "drug_b": [
            "phenelzine", "tranylcypromine",
            "isocarboxazid", "selegiline", "maoi",
        ],
        "severity": "danger",
        "description": (
            "Risk of serotonin syndrome. Allow"
            " at least 14-day washout between MAOIs"
            " and venlafaxine."
        ),
        "source": "FDA Drug Label",
    },
    # Methotrexate + Trimethoprim
    {
        "drug_a": ["methotrexate", "trexall"],
        "drug_b": [
            "trimethoprim", "bactrim",
            "sulfamethoxazole-trimethoprim", "tmp-smx",
        ],
        "severity": "danger",
        "description": (
            "Both are folate antagonists. Combined use"
            " increases risk of severe pancytopenia"
            " and bone marrow suppression."
        ),
        "source": "FDA Drug Label / BMJ",
    },
    # Potassium + NSAIDs
    {
        "drug_a": ["potassium", "potassium chloride", "potassium supplement"],
        "drug_b": [
            "ibuprofen", "naproxen", "nsaid",
            "diclofenac", "indomethacin",
        ],
        "severity": "caution",
        "description": (
            "NSAIDs reduce renal potassium excretion."
            " Combined with potassium supplements,"
            " hyperkalemia risk increases."
        ),
        "source": "FDA Drug Label",
    },
    # Doxycycline + Isotretinoin
    {
        "drug_a": ["doxycycline", "tetracycline", "minocycline"],
        "drug_b": ["isotretinoin", "accutane", "claravis"],
        "severity": "danger",
        "description": (
            "Both can cause intracranial hypertension"
            " (pseudotumor cerebri)."
            " Combination is contraindicated."
        ),
        "source": "FDA Drug Label",
    },
    # Theophylline + Fluvoxamine
    {
        "drug_a": ["theophylline", "aminophylline"],
        "drug_b": ["fluvoxamine", "luvox"],
        "severity": "danger",
        "description": (
            "Fluvoxamine is a potent CYP1A2 inhibitor,"
            " increasing theophylline levels 3-fold."
            " Risk of seizures and arrhythmias."
        ),
        "source": "FDA Drug Label",
    },
    # Colchicine + Clarithromycin
    {
        "drug_a": ["colchicine", "colcrys"],
        "drug_b": ["clarithromycin", "biaxin"],
        "severity": "danger",
        "description": (
            "Clarithromycin inhibits CYP3A4 and P-gp,"
            " increasing colchicine to toxic levels."
            " Fatal cases reported."
        ),
        "source": "FDA Drug Safety Communication",
    },
    # Ergotamine + CYP3A4 inhibitors
    {
        "drug_a": [
            "ergotamine", "dihydroergotamine",
            "ergot alkaloid",
        ],
        "drug_b": [
            "ketoconazole", "itraconazole",
            "clarithromycin", "erythromycin",
            "ritonavir",
        ],
        "severity": "danger",
        "description": (
            "CYP3A4 inhibition increases ergot levels,"
            " risking ergotism (vasospasm, ischemia,"
            " gangrene). Contraindicated."
        ),
        "source": "FDA Drug Label",
    },
    # Dabigatran + Ketoconazole
    {
        "drug_a": ["dabigatran", "pradaxa"],
        "drug_b": ["ketoconazole", "nizoral"],
        "severity": "danger",
        "description": (
            "Ketoconazole inhibits P-glycoprotein,"
            " increasing dabigatran exposure and"
            " risk of major bleeding."
        ),
        "source": "FDA Drug Label",
    },
    # Rivaroxaban + CYP3A4 inhibitors
    {
        "drug_a": ["rivaroxaban", "xarelto"],
        "drug_b": [
            "ketoconazole", "itraconazole",
            "ritonavir", "clarithromycin",
        ],
        "severity": "danger",
        "description": (
            "Strong CYP3A4/P-gp inhibitors increase"
            " rivaroxaban levels, increasing bleeding risk."
            " Avoid concurrent use."
        ),
        "source": "FDA Drug Label",
    },
    # Apixaban + Strong CYP3A4 inhibitors
    {
        "drug_a": ["apixaban", "eliquis"],
        "drug_b": [
            "ketoconazole", "itraconazole",
            "ritonavir", "clarithromycin",
        ],
        "severity": "warning",
        "description": (
            "Strong CYP3A4/P-gp inhibitors increase"
            " apixaban exposure. Reduce apixaban dose"
            " by 50% if on standard dosing."
        ),
        "source": "FDA Drug Label",
    },
    # Fexofenadine + Grapefruit/Apple/Orange juice
    {
        "drug_a": ["fexofenadine", "allegra"],
        "drug_b": [
            "grapefruit juice", "apple juice",
            "orange juice",
        ],
        "severity": "caution",
        "description": (
            "Fruit juices inhibit OATP transporters,"
            " reducing fexofenadine absorption by up to 70%."
            " Take with water only."
        ),
        "source": "Clin Pharmacol Ther / FDA Drug Label",
    },
    # Vitamin D + Thiazide diuretics
    {
        "drug_a": ["vitamin d", "cholecalciferol", "ergocalciferol"],
        "drug_b": [
            "hydrochlorothiazide", "hctz",
            "chlorthalidone", "thiazide",
        ],
        "severity": "caution",
        "description": (
            "Thiazides reduce calcium excretion."
            " With high-dose vitamin D, risk of"
            " hypercalcemia. Monitor calcium levels."
        ),
        "source": "NIH / Endocrine Practice",
    },
]


@CheckRegistry.register
class DrugInteractionCheck(BaseCheck):
    """Detects mentions of known dangerous drug-drug or drug-supplement interactions."""

    name = "drug_interaction"
    description = (
        "Flags text that mentions known dangerous"
        " drug/supplement combinations"
        " without adequate warnings."
    )

    def run(self, text: str, config: GuardConfig) -> CheckResult:
        text_lower = text.lower()
        found_interactions: list[dict] = []

        for interaction in _KNOWN_INTERACTIONS:
            a_names = interaction["drug_a"]
            b_names = interaction["drug_b"]

            a_found = any(name in text_lower for name in a_names)
            b_found = any(name in text_lower for name in b_names)

            if a_found and b_found:
                # Check if there's already a warning/caution in the text
                has_warning = any(
                    w in text_lower
                    for w in [
                        "risk", "danger", "caution", "warning", "avoid",
                        "do not", "don't", "should not", "consult",
                        "위험", "주의", "금지", "피하", "상담",
                        "リスク", "危険", "注意", "避け",
                    ]
                )

                # If the text already warns about the interaction, reduce severity
                effective_severity = interaction["severity"]
                if has_warning and effective_severity == "danger":
                    effective_severity = "warning"
                elif has_warning and effective_severity == "warning":
                    effective_severity = "caution"

                a_match = next(n for n in a_names if n in text_lower)
                b_match = next(n for n in b_names if n in text_lower)

                found_interactions.append({
                    "drug_a": a_match,
                    "drug_b": b_match,
                    "severity": effective_severity,
                    "description": interaction["description"],
                    "source": interaction["source"],
                    "has_warning": has_warning,
                })

        if not found_interactions:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASS,
                severity=Severity.INFO,
                message="No known drug interactions detected.",
            )

        max_severity = Severity.INFO
        for item in found_interactions:
            sev = Severity(item["severity"])
            if sev > max_severity:
                max_severity = sev

        pairs = [f"{i['drug_a']}+{i['drug_b']}" for i in found_interactions[:3]]
        suffix = f" (+{len(found_interactions) - 3} more)" if len(found_interactions) > 3 else ""

        warn_note = ""
        all_warned = all(i["has_warning"] for i in found_interactions)
        if all_warned:
            warn_note = " (text includes warnings)"

        status = (
            CheckStatus.FAIL
            if max_severity >= Severity.WARNING and not all_warned
            else CheckStatus.WARNING
        )

        return CheckResult(
            check_name=self.name,
            status=status,
            severity=max_severity,
            message=f"Known interaction detected: {', '.join(pairs)}{suffix}{warn_note}",
            details={
                "interactions": found_interactions,
                "recommendation": (
                    "Ensure adequate warnings are included"
                    " when discussing drug interactions."
                ),
            },
        )

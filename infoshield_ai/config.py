"""Configuration constants for InfoShield AI."""

from pathlib import Path

# Project Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Model Configuration
# gemini-2.5-flash: Stable, supports google_search + function calling
MODEL_ID = "gemini-2.5-flash"
# gemini-2.5-flash: Faster, cost-effective for lightweight tasks
MODEL_ID_FAST = "gemini-2.5-flash"

# Application Identifiers
APP_NAME = "infoshield_ai"
DEFAULT_USER_ID = "default_user"

# Decision Thresholds
URGENCY_THRESHOLD = 8  # Score >= 8 triggers immediate response
CREDIBILITY_THRESHOLD = 60  # Score >= 60% enables automated response

# Session Configuration
SESSION_TTL_DAYS = 15  # For future Redis integration

# Data Paths
PENDING_VERIFICATIONS_PATH = DATA_DIR / "pending_verifications.csv"

# Disaster Keywords for Enhanced Detection
DISASTER_KEYWORDS = [
    "flood", "flooding", "earthquake", "tsunami", "cyclone", "hurricane",
    "tornado", "wildfire", "fire", "landslide", "avalanche", "drought",
    "volcano", "eruption", "storm", "typhoon", "blizzard", "heatwave",
    "rescue", "emergency", "evacuation", "trapped", "help", "sos"
]

# Official Disaster Management Sources
OFFICIAL_SOURCES = [
    # Global Organizations
    "un ocha", "red cross", "red crescent", "world meteorological organization",
    "international federation", "unicef", "who",

    # News Agencies
    "reuters", "ap news", "afp", "bbc", "cnn", "al jazeera",

    # Weather Services
    "accuweather", "weather.com", "weather underground",

    # India
    "ndrf", "ndma", "imd", "indian meteorological department", "india met",
    "sdma", "ddma", "ndtv", "times of india", "hindustan times",

    # United States
    "fema", "nws", "national weather service", "noaa", "usgs",
    "national hurricane center", "storm prediction center",

    # United Kingdom
    "met office", "environment agency", "bbc weather",

    # Australia
    "bureau of meteorology", "bom", "ses", "emergency victoria",

    # Japan
    "jma", "japan meteorological agency", "data.jma.go.jp", "jma.go.jp",
    "japan earthquake", "japan tsunami warning",

    # China
    "cma", "china meteorological administration",

    # European Union
    "eumetsat", "copernicus", "ecmwf",

    # Philippines
    "pagasa", "ndrrmc", "philvolcs",

    # Bangladesh
    "bmd", "bangladesh meteorological department",

    # Generic Official Terms
    "government", "official", "ministry", "department",
    "meteorological", "seismological", "emergency management",
    "civil defense", "disaster management authority"
]

# Official Twitter/X Handles for Disaster Management Agencies
OFFICIAL_TWITTER_HANDLES = {
    # Global Organizations
    "global": [
        "@WMO", "@WHO", "@UNOCHA", "@IFRC", "@FAO", "@WFP",
        "@UNDRR", "@UNHCR", "@UN_Water",
    ],

    # India
    "india": [
        "@ndmaindia",       # National Disaster Management Authority
        "@NDRFHQ",          # National Disaster Response Force
        "@Indiametdept",    # India Meteorological Dept (IMD)
        "@PMOIndia",        # Prime Minister's Office
        "@HMOIndia",        # Home Minister's Office
        "@PIB_India",       # Press Information Bureau
        "@IndianArmy",      # Indian Army
    ],

    # United States
    "usa": [
        "@FEMA", "@NWS", "@NOAA", "@USGS", "@NHC_Atlantic", "@NHC_Pacific",
        "@CDCemergency", "@DHSgov", "@EPA", "@RedCross", "@Readygov",
    ],

    # United Kingdom
    "uk": [
        "@metoffice", "@EnvAgency", "@DefraGovUK", "@cabinetofficeuk",
        "@BritishRedCross", "@MCA_media",
        "@EnvAgency",       # Environment Agency (Floodline)
    ],

    # Australia
    "australia": [
        "@BOM_au",          # Bureau of Meteorology
        "@vicsesnews",      # Victoria SES
        "@NSWSES",          # NSW SES
        "@QldFES",          # Queensland Fire & Emergency
        "@dfes_wa",         # WA Dept of Fire & Emergency
        "@AIDR_News",
        "@RedCrossAU",
        "@ABCemergency",
    ],

    # Japan
    "japan": [
        "@JMA_kishou",      # Japan Meteorological Agency
        "@FDMA_JAPAN",      # Fire & Disaster Management Agency
        "@CAO_BOUSAI",      # Cabinet Office Disaster Management
        "@JapanSafeTravel",  # Japan Tourism Agency Safety
        "@Aborستان_Japan",  # Japan Coast Guard (if available)
    ],

    # Japan Official Data Sources (non-Twitter)
    # - https://www.data.jma.go.jp/ (JMA Open Data Portal)
    # - https://www.jma.go.jp/bosai/ (JMA Disaster Prevention Info)

    # Philippines
    "philippines": [
        "@dost_pagasa",     # PAGASA
        "@NDRRMC",          # National Disaster Risk Reduction & Mgmt Council
        "@philredcross",    # Philippine Red Cross
        "@phivolcs_dost",   # Volcano & Seismology
    ],

    # Indonesia
    "indonesia": [
        "@infoBMKG",        # Meteorology, Climatology, and Geophysical Agency
        "@BNPB_Indonesia",  # National Disaster Mgmt Agency
        "@palangmerah",     # Indonesian Red Cross (PMI)
    ],

    # Bangladesh
    "bangladesh": [
        "@BDRCS1",          # Bangladesh Red Crescent Society
        "@MoDMR_Govt",      # Ministry of Disaster Management
        "@bmdweather",      # Bangladesh Meteorological Dept
    ],

    # Canada
    "canada": [
        "@environmentca",   # Environment Canada
        "@RedCrossCanada",
        "@EmergOntario",
        "@BCGovFireInfo",
    ],

    # European Union
    "eu": [
        "@CopernicusEU", "@ECMWF", "@EU_ECHO", "@eumetsat",
    ],

    # Mexico
    "mexico": [
        "@CruzRoja_MX",     # Mexican Red Cross
        "@conagua_mx",      # National Water Commission
        "@CNPC_MX",         # Civil Protection
        "@SEGOB_mx",
    ],

    # Brazil
    "brazil": [
        "@defesacivilbr",   # Civil Defense
        "@inmet_",          # National Institute of Meteorology
        "@inpe_mct",        # Space Research (Satellite monitoring)
    ],

    # Nepal
    "nepal": [
        "@NRCS_Nepal",      # Nepal Red Cross
        "@DHM_Weather",     # Dept of Hydrology & Meteorology
        "@NDRRMA_Nepal",    # National Disaster Risk Reduction & Management Authority
    ],

    # Sri Lanka
    "srilanka": [
        "@SLRedCross",      # Sri Lanka Red Cross
        "@dmc_lk",          # Disaster Management Centre
        "@SLMetDept",       # Dept of Meteorology
    ],
}

# Official Government Data Portals for Disaster Verification
OFFICIAL_DATA_PORTALS = {
    "japan": {
        "jma_data": "https://www.data.jma.go.jp/",          # JMA Open Data Portal
        "jma_bosai": "https://www.jma.go.jp/bosai/",        # JMA Disaster Prevention
        "jma_earthquake": "https://www.jma.go.jp/bosai/map.html#contents=earthquake_map",
    },
    "usa": {
        "usgs_earthquake": "https://earthquake.usgs.gov/earthquakes/map/",
        "noaa_weather": "https://www.weather.gov/",
        "nhc_hurricanes": "https://www.nhc.noaa.gov/",
    },
    "india": {
        "imd": "https://mausam.imd.gov.in/",
        "ndma": "https://ndma.gov.in/",
        "imd_cyclone": "https://rsmcnewdelhi.imd.gov.in/",
    },
    "australia": {
        "bom": "http://www.bom.gov.au/",
        "ga_earthquake": "https://earthquakes.ga.gov.au/",
    },
    "uk": {
        "met_office": "https://www.metoffice.gov.uk/",
        "flood_info": "https://check-for-flooding.service.gov.uk/",
    },
    "philippines": {
        "pagasa": "https://www.pagasa.dost.gov.ph/",
        "phivolcs": "https://www.phivolcs.dost.gov.ph/",
    },
    "indonesia": {
        "bmkg": "https://www.bmkg.go.id/",
    },
    "bangladesh": {
        "bmd": "https://www.bmd.gov.bd/",
    },
}

# Twitter Search Patterns for Disaster Verification
TWITTER_SEARCH_PATTERNS = [
    # Site-specific searches are very effective
    "site:twitter.com {location} {disaster_type}",
    "site:x.com {location} {disaster_type} alert",

    # Combine verified handle with disaster keywords
    # Use 'from:' to search only BY that agency
    "from:{twitter_handle} {disaster_type}",

    # Broader keyword search (good for discovery)
    "{location} {disaster_type} official report",
]

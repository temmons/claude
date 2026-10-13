"""Zoning sources for each DuPage County municipality.

MUNICIPALITY values match the MUNICIPALITY field on the county parcel layer.
`field` is the zoning-district attribute; `where` filters out superseded or
out-of-town features; `join` is "spatial" (parcel interior point falls in the
zoning polygon) or "pin" (attribute join on the 10-digit PIN).
"""
GISC = "https://ags.gisconsortium.org/arcgis/rest/services"

SOURCES = {
    "Uninc": dict(url="https://gis.dupageco.org/arcgis/rest/services/Zoning/UnincorporatedZoningData/MapServer/0", field="ZONING"),
    "Aurora": dict(url="https://gis.aurora.il.us/arcgis/rest/services/MyPlace/MyPlace/MapServer/22", field="ZONING", join="pin", where="COUNTY = 'DUPAGE' OR COUNTY IS NULL"),
    "Bartlett": dict(url="https://maps.vbartlett.org/server/rest/services/All_Data_Public/FeatureServer/102", field="ZONECLASS"),
    "Bensenville": dict(url=f"{GISC}/VBV/AGOL_VBV_Project/MapServer/0", field="ZONED"),
    "Bloomingdale": dict(url="https://services6.arcgis.com/nHwZFPzhWRbCrBdy/arcgis/rest/services/Zoning_Boundaries/FeatureServer/16", field="ZONING_DISTRICT"),
    "Burr Ridge": dict(url="https://services1.arcgis.com/55JaHxBzqQBTWeG7/arcgis/rest/services/Zoning_(Public_View)/FeatureServer/1", field="ThemeDist"),
    "Carol Stream": dict(url="https://services5.arcgis.com/74bZbbuf05Ctvbzv/arcgis/rest/services/Carol_Stream_Zoning_Districts/FeatureServer/0", field="ZONED"),
    "Clarendon Hills": dict(url="https://services5.arcgis.com/cnI60UwnKJOhQqOd/arcgis/rest/services/ClarendonHillsInteractiveZoningMap2020/FeatureServer/4", field="LandUse"),
    "Darien": dict(url="https://services2.arcgis.com/ujU8BLaouMWRzTbX/arcgis/rest/services/Darien_Zoning_Map_2022/FeatureServer/8", field="ZONING_CLASS_2018"),
    "Downers Grove": dict(url="https://parcels.downers.us/arcgis/rest/services/Zoning/MapServer/5", field="ZONING"),
    "Elmhurst": dict(url=f"{GISC}/CEH/AGOL_CEH_Project/MapServer/0", field="ZONED"),
    "Glen Ellyn": dict(url=f"{GISC}/VGE/AGOL_VGE_Project/MapServer/0", field="ZONED"),
    "Glendale Heights": dict(url=f"{GISC}/VGH/AGOL_VGH_Project/MapServer/0", field="ZONED"),
    "Hanover Park": dict(url=f"{GISC}/VHP/AGOL_VHP_Project/MapServer/0", field="ZONED"),
    "Lisle": dict(url="https://vhgis.villageoflisle.org/arcgis/rest/services/Public/ZONING/FeatureServer/0", field="ZONE_CODE"),
    "Lombard": dict(url="https://services6.arcgis.com/vs0Q5ds549q7lQMm/arcgis/rest/services/Zoning/FeatureServer/0", field="Zoning"),
    "Naperville": dict(url="https://portal.naperville.il.us/arcgis/rest/services/GTX/YourPlace/MapServer/21", field="ZONING_CODE"),
    "Oak Brook": dict(url="https://utility.arcgis.com/usrsvcs/servers/df29c9991bc848b08589b580aeac9789/rest/services/Oakbrook/GHA_OakBrook_Online/MapServer/11", field="ZONED"),
    "Roselle": dict(url=f"{GISC}/VRO/AGOL_VRO_Project/MapServer/0", field="ZONED"),
    "Villa Park": dict(url="https://utility.arcgis.com/usrsvcs/servers/c296f22648eb4511bfe2fd9e2557c7b8/rest/services/ENG_Zoning/Zoning_Districts/MapServer/0", field="ZONING_CODE"),
    "Warrenville": dict(url="https://services5.arcgis.com/TkBKgQn8d3sPkMZo/arcgis/rest/services/Base_Data_Public/FeatureServer/1", field="LocalDat_2"),
    "West Chicago": dict(url="https://services1.arcgis.com/m5a11YBVmO0IIPPX/arcgis/rest/services/2025_WC_Zoning_service/FeatureServer/0", field="ZONING"),
    "Westmont": dict(url="https://services5.arcgis.com/XWUAZV69Zk3cPZHa/arcgis/rest/services/Zoning_PublicView/FeatureServer/0", field="ZONE2026"),
    "Wheaton": dict(url="https://services2.arcgis.com/YyIQHvpylgCY7DEY/arcgis/rest/services/Zoning/FeatureServer/0", field="ZONING"),
    "Willowbrook": dict(url=f"{GISC}/VWB/AGOL_VWB_Project/MapServer/0", field="ZONED"),
    "Wood Dale": dict(url="https://services3.arcgis.com/gtOFGDNHdftP2Pps/arcgis/rest/services/CommunityDevelopment/FeatureServer/0", field="TCC_Zoning"),
    "Woodridge": dict(url=f"{GISC}/VWR/AGOL_VWR_Project/MapServer/2", field="ZONED"),
}

# Towns in the county parcel layer with no published GIS zoning layer found.
NO_GIS_ZONING = ["Addison", "Hinsdale", "Itasca", "Winfield", "Oakbrook Terrace", "Wayne",
                 "Bolingbrook", "Chicago", "St Charles", "Elk Grove", "Lemont", "Schaumburg", "Batavia"]

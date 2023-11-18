from qgis import processing
from qgis.core import QgsFeature, QgsGeometry, QgsProcessingOutputLayerDefinition, QgsVectorLayer

import pytest

from src.algorithm import Algorithm


LINES = (
    "LineString (3569791.65918140485882759 6347785.93876876402646303, 3569817.29298910731449723 6347770.60050677787512541, 3569817.92332864087074995 6347761.98586648423224688)",
    "MultiLineString ((3569750.02604898577556014 6347792.64984573982656002, 3569750.17273568129166961 6347769.28457224369049072, 3569726.80746218701824546 6347769.13788554817438126, 3569726.66077548963949084 6347792.50315904431045055, 3569750.02604898577556014 6347792.64984573982656002))",
)
POLYGONS = (
    "Polygon ((3569749.9001297322101891 6347764.61510257329791784, 3569757.48407261306419969 6347754.47326962277293205, 3569749.63190319808200002 6347755.34239032585173845, 3569745.74189351173117757 6347761.38562505599111319, 3569749.9001297322101891 6347764.61510257329791784))",
    "MultiPolygon (((3569812.3302051005885005 6347791.8438609205186367, 3569833.55163606768473983 6347792.89442680962383747, 3569829.3493725098669529 6347787.64159736316651106, 3569815.06167641328647733 6347786.59103147312998772, 3569812.3302051005885005 6347791.8438609205186367)),((3569818.83459341339766979 6347801.96099858731031418, 3569826.14707991806790233 6347798.54850488528609276, 3569820.5408402644097805 6347798.79225443582981825, 3569818.83459341339766979 6347801.96099858731031418)))",
    "Polygon ((3569756.58066737465560436 6347794.25127100665122271, 3569766.91023893468081951 6347786.92509078793227673, 3569759.17007119115442038 6347785.3434022506698966, 3569753.61368533130735159 6347789.90184908546507359, 3569756.58066737465560436 6347794.25127100665122271))",
    "MultiPolygon (((3569729.18042284436523914 6347796.32892546802759171, 3569724.50720768235623837 6347808.09897327050566673, 3569731.86016463674604893 6347805.21003586146980524, 3569734.03756839968264103 6347798.36081881076097488, 3569729.18042284436523914 6347796.32892546802759171)))",
    "MultiPolygon (((3569722.45611009420827031 6347771.28532140143215656, 3569710.86980802612379193 6347766.17351451888680458, 3569713.48065453907474875 6347773.62974787130951881, 3569720.24329600436612964 6347776.06275871675461531, 3569722.45611009420827031 6347771.28532140143215656)))",
    "MultiPolygon (((3569753.39613456837832928 6347782.79288418311625719, 3569761.50192580418661237 6347782.53140704613178968, 3569752.61170315882191062 6347779.65515854395925999, 3569753.39613456837832928 6347782.79288418311625719)))",
    "MultiPolygon (((3569753.13465743185952306 6347770.89567446615546942, 3569752.08874888531863689 6347773.379707264713943, 3569762.15561864571645856 6347768.15016453247517347, 3569753.13465743185952306 6347770.89567446615546942)))",
    "MultiPolygon (((3569738.04293423052877188 6347795.70041574910283089, 3569737.29699251614511013 6347803.77604531031101942, 3569741.25372670777142048 6347795.31122879404574633, 3569738.04293423052877188 6347795.70041574910283089)))",
    "MultiPolygon (((3569739.92251957906410098 6347764.54570444952696562, 3569739.96497977105900645 6347756.43580808863043785, 3569736.75760231213644147 6347765.212002819404006, 3569739.92251957906410098 6347764.54570444952696562)))",
    "MultiPolygon (((3569722.41109387902542949 6347780.70106708910316229, 3569714.3053026432171464 6347780.9625442260876298, 3569723.19552528858184814 6347783.83879272826015949, 3569722.41109387902542949 6347780.70106708910316229)))",
    "MultiPolygon (((3569729.28231467353180051 6347765.00057455152273178, 3569731.90566611709073186 6347765.61893596407026052, 3569725.07520849397405982 6347756.56162771955132484, 3569729.28231467353180051 6347765.00057455152273178)))",
    "MultiPolygon (((3569723.18460257723927498 6347791.01382320839911699, 3569723.619303940795362 6347788.3538648709654808, 3569715.0581711046397686 6347795.79678019601851702, 3569723.18460257723927498 6347791.01382320839911699)))",
    "MultiPolygon (((3569747.66514745121821761 6347795.68019161652773619, 3569745.13767131650820374 6347794.74413178022950888, 3569750.80329665401950479 6347804.57218720857053995, 3569747.66514745121821761 6347795.68019161652773619)))",
)


@pytest.mark.parametrize(
    "lines, polys, expected, _rotated, distance, angle, longest, no_multi",
    [
        (
            LINES,
            POLYGONS,
            [
                "Polygon ((3569753.58864819118753076 6347764.11446942016482353, 3569753.43699399335309863 6347751.45153270661830902, 3569747.73413696372881532 6347756.91864867601543665, 3569748.32373024383559823 6347764.08141637593507767, 3569753.58864819118753076 6347764.11446942016482353))",
                "MultiPolygon (((3569813.25820143055170774 6347786.38722559250891209, 3569830.7760964990593493 6347798.41120884940028191, 3569829.95292756427079439 6347791.73486036341637373, 3569818.33871932420879602 6347783.34724357444792986, 3569813.25820143055170774 6347786.38722559250891209)),((3569813.49043578421697021 6347798.41259914636611938, 3569821.50627558259293437 6347799.3420530017465353, 3569816.6050431989133358 6347796.60942459385842085, 3569813.49043578421697021 6347798.41259914636611938)))",
                "Polygon ((3569754.19176710862666368 6347791.75986070372164249, 3569766.8547038221731782 6347791.60820650681853294, 3569761.38758785324171185 6347785.90534947626292706, 3569754.22482015285640955 6347786.49494275636970997, 3569754.19176710862666368 6347791.75986070372164249))",
                "MultiPolygon (((3569727.01503511192277074 6347796.92115118075162172, 3569727.16668931068852544 6347809.58408789522945881, 3569732.86954633938148618 6347804.11697192490100861, 3569732.27995305927470326 6347796.95420422591269016, 3569727.01503511192277074 6347796.92115118075162172)))",
                "MultiPolygon (((3569721.85230995062738657 6347768.90268314443528652, 3569709.18937323708087206 6347769.05433734226971865, 3569714.65648920647799969 6347774.75719437096267939, 3569721.81925690639764071 6347774.16760109178721905, 3569721.85230995062738657 6347768.90268314443528652)))",
                "MultiPolygon (((3569753.19105820776894689 6347782.15055817645043135, 3569761.10734268836677074 6347783.91256324574351311, 3569753.21136263431981206 6347778.91632835194468498, 3569753.19105820776894689 6347782.15055817645043135)))",
                "MultiPolygon (((3569753.36986791715025902 6347771.90524543728679419, 3569753.35294756107032299 6347774.60043695848435163, 3569760.6562094846740365 6347765.91986386384814978, 3569753.36986791715025902 6347771.90524543728679419)))",
                "MultiPolygon (((3569738.37380956672132015 6347795.61703364830464125, 3569736.61180449742823839 6347803.53331813029944897, 3569741.60803938983008265 6347795.63733807578682899, 3569738.37380956672132015 6347795.61703364830464125)))",
                "MultiPolygon (((3569739.37244213931262493 6347764.7100347550585866, 3569741.13444720720872283 6347756.79375027399510145, 3569736.13821231527253985 6347764.68973032850772142, 3569739.37244213931262493 6347764.7100347550585866)))",
                "MultiPolygon (((3569722.61617023963481188 6347781.34339309670031071, 3569714.69988575857132673 6347779.58138802647590637, 3569722.59586581215262413 6347784.57762292120605707, 3569722.61617023963481188 6347781.34339309670031071)))",
                "MultiPolygon (((3569729.85112644545733929 6347764.81685314979404211, 3569732.54631796572357416 6347764.83377350494265556, 3569723.86574487388134003 6347757.5305115794762969, 3569729.85112644545733929 6347764.81685314979404211)))",
                "MultiPolygon (((3569723.04383294470608234 6347790.62475940771400928, 3569723.0607532998546958 6347787.92956788651645184, 3569715.75749137718230486 6347796.61014098115265369, 3569723.04383294470608234 6347790.62475940771400928)))",
                "MultiPolygon (((3569746.77197512239217758 6347795.90902979858219624, 3569744.07678360305726528 6347795.89210944250226021, 3569752.75735669769346714 6347803.19537136517465115, 3569746.77197512239217758 6347795.90902979858219624)))",
            ],
            [1 for _ in range(len(POLYGONS))],
            0.0,
            89.9,
            False,
            False,
        ),
        (
            LINES,
            POLYGONS,
            [
                "Polygon ((3569745.77356627164408565 6347761.41495595872402191, 3569758.43716152291744947 6347761.49445774406194687, 3569753.07504793582484126 6347755.69276202656328678, 3569745.90271191857755184 6347756.15151840355247259, 3569745.77356627164408565 6347761.41495595872402191))",
                "MultiPolygon (((3569814.79303046176210046 6347797.45070173405110836, 3569832.75941926566883922 6347786.10778789594769478, 3569826.30093402834609151 6347784.22651049960404634, 3569814.00737850228324533 6347791.58249044511467218, 3569814.79303046176210046 6347797.45070173405110836)),((3569825.93200115626677871 6347801.98797776363790035, 3569829.95250821439549327 6347794.99132891371846199, 3569825.50592205254361033 6347798.41436972469091415, 3569825.93200115626677871 6347801.98797776363790035)))",
                "Polygon ((3569761.49256450450047851 6347794.57200548611581326, 3569762.45952894585207105 6347781.945131566375494, 3569756.29624481918290257 6347786.88738450407981873, 3569756.25112592102959752 6347794.07423538994044065, 3569761.49256450450047851 6347794.57200548611581326))",
                "MultiPolygon (((3569734.83011703193187714 6347799.62066464032977819, 3569722.16652178019285202 6347799.54116285499185324, 3569727.52863536775112152 6347805.3428585734218359, 3569734.70097138546407223 6347804.88410219643265009, 3569734.83011703193187714 6347799.62066464032977819)))",
                "MultiPolygon (((3569719.15279649011790752 6347776.71776506491005421, 3569719.23229827545583248 6347764.05416981317102909, 3569713.43060255795717239 6347769.41628340072929859, 3569713.8893589349463582 6347776.58861941751092672, 3569719.15279649011790752 6347776.71776506491005421)))",
                "MultiPolygon (((3569754.01973922271281481 6347779.675196866504848, 3569756.71568226162344217 6347787.32399500627070665, 3569756.77434204705059528 6347777.98025789763778448, 3569754.01973922271281481 6347779.675196866504848)))",
                "MultiPolygon (((3569754.62984171323478222 6347773.20047478191554546, 3569756.33898312412202358 6347775.28450435772538185, 3569756.41020012274384499 6347763.94056711811572313, 3569754.62984171323478222 6347773.20047478191554546)))",
                "MultiPolygon (((3569740.84917087573558092 6347796.44571466371417046, 3569733.20037273596972227 6347799.14165770169347525, 3569742.54410984460264444 6347799.20031748618930578, 3569740.84917087573558092 6347796.44571466371417046)))",
                "MultiPolygon (((3569736.89708083029836416 6347763.88135374058037996, 3569744.54587897006422281 6347761.1854107016697526, 3569735.20214186329394579 6347761.12675091624259949, 3569736.89708083029836416 6347763.88135374058037996)))",
                "MultiPolygon (((3569721.78748922143131495 6347783.8187544047832489, 3569719.09154618438333273 6347776.16995626501739025, 3569719.03288639802485704 6347785.51369337365031242, 3569721.78748922143131495 6347783.8187544047832489)))",
                "MultiPolygon (((3569731.14635579101741314 6347763.55687935277819633, 3569733.23038536589592695 6347761.84773794189095497, 3569721.88644812535494566 6347761.77652094140648842, 3569731.14635579101741314 6347763.55687935277819633)))",
                "MultiPolygon (((3569721.78385914769023657 6347789.32953006215393543, 3569720.07471773773431778 6347787.24550048634409904, 3569720.00350073724985123 6347798.58943772595375776, 3569721.78385914769023657 6347789.32953006215393543)))",
                "MultiPolygon (((3569745.47674577869474888 6347797.16900359652936459, 3569743.39271620288491249 6347798.8781450055539608, 3569754.73665344342589378 6347798.94936200510710478, 3569745.47674577869474888 6347797.16900359652936459)))",
            ],
            [1 for _ in range(len(POLYGONS))],
            0.0,
            89.9,
            True,
            False,
        ),
        (
            LINES,
            POLYGONS,
            [
                "Polygon ((3569749.9001297322101891 6347764.61510257329791784, 3569757.48407261306419969 6347754.47326962277293205, 3569749.63190319808200002 6347755.34239032585173845, 3569745.74189351173117757 6347761.38562505599111319, 3569749.9001297322101891 6347764.61510257329791784))",
                "MultiPolygon (((3569812.3302051005885005 6347791.8438609205186367, 3569833.55163606768473983 6347792.89442680962383747, 3569829.3493725098669529 6347787.64159736316651106, 3569815.06167641328647733 6347786.59103147312998772, 3569812.3302051005885005 6347791.8438609205186367)),((3569818.83459341339766979 6347801.96099858731031418, 3569826.14707991806790233 6347798.54850488528609276, 3569820.5408402644097805 6347798.79225443582981825, 3569818.83459341339766979 6347801.96099858731031418)))",
                "Polygon ((3569756.58066737465560436 6347794.25127100665122271, 3569766.91023893468081951 6347786.92509078793227673, 3569759.17007119115442038 6347785.3434022506698966, 3569753.61368533130735159 6347789.90184908546507359, 3569756.58066737465560436 6347794.25127100665122271))",
                "MultiPolygon (((3569729.18042284436523914 6347796.32892546802759171, 3569724.50720768235623837 6347808.09897327050566673, 3569731.86016463674604893 6347805.21003586146980524, 3569734.03756839968264103 6347798.36081881076097488, 3569729.18042284436523914 6347796.32892546802759171)))",
                "MultiPolygon (((3569722.45611009420827031 6347771.28532140143215656, 3569710.86980802612379193 6347766.17351451888680458, 3569713.48065453907474875 6347773.62974787130951881, 3569720.24329600436612964 6347776.06275871675461531, 3569722.45611009420827031 6347771.28532140143215656)))",
                "MultiPolygon (((3569753.19105820776894689 6347782.15055817645043135, 3569761.10734268836677074 6347783.91256324574351311, 3569753.21136263431981206 6347778.91632835194468498, 3569753.19105820776894689 6347782.15055817645043135)))",
                "MultiPolygon (((3569753.13465743185952306 6347770.89567446615546942, 3569752.08874888531863689 6347773.379707264713943, 3569762.15561864571645856 6347768.15016453247517347, 3569753.13465743185952306 6347770.89567446615546942)))",
                "MultiPolygon (((3569738.37380956672132015 6347795.61703364830464125, 3569736.61180449742823839 6347803.53331813029944897, 3569741.60803938983008265 6347795.63733807578682899, 3569738.37380956672132015 6347795.61703364830464125)))",
                "MultiPolygon (((3569739.37244213931262493 6347764.7100347550585866, 3569741.13444720720872283 6347756.79375027399510145, 3569736.13821231527253985 6347764.68973032850772142, 3569739.37244213931262493 6347764.7100347550585866)))",
                "MultiPolygon (((3569722.61617023963481188 6347781.34339309670031071, 3569714.69988575857132673 6347779.58138802647590637, 3569722.59586581215262413 6347784.57762292120605707, 3569722.61617023963481188 6347781.34339309670031071)))",
                "MultiPolygon (((3569729.85112644545733929 6347764.81685314979404211, 3569732.54631796572357416 6347764.83377350494265556, 3569723.86574487388134003 6347757.5305115794762969, 3569729.85112644545733929 6347764.81685314979404211)))",
                "MultiPolygon (((3569723.04383294470608234 6347790.62475940771400928, 3569723.0607532998546958 6347787.92956788651645184, 3569715.75749137718230486 6347796.61014098115265369, 3569723.04383294470608234 6347790.62475940771400928)))",
                "MultiPolygon (((3569747.66514745121821761 6347795.68019161652773619, 3569745.13767131650820374 6347794.74413178022950888, 3569750.80329665401950479 6347804.57218720857053995, 3569747.66514745121821761 6347795.68019161652773619)))",
            ],
            [0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 0],
            10.5,
            15.5,
            False,
            False,
        ),
        (
            LINES,
            POLYGONS,
            [
                "Polygon ((3569753.58864819118753076 6347764.11446942016482353, 3569753.43699399335309863 6347751.45153270661830902, 3569747.73413696372881532 6347756.91864867601543665, 3569748.32373024383559823 6347764.08141637593507767, 3569753.58864819118753076 6347764.11446942016482353))",
                "MultiPolygon (((3569812.3302051005885005 6347791.8438609205186367, 3569833.55163606768473983 6347792.89442680962383747, 3569829.3493725098669529 6347787.64159736316651106, 3569815.06167641328647733 6347786.59103147312998772, 3569812.3302051005885005 6347791.8438609205186367)),((3569818.83459341339766979 6347801.96099858731031418, 3569826.14707991806790233 6347798.54850488528609276, 3569820.5408402644097805 6347798.79225443582981825, 3569818.83459341339766979 6347801.96099858731031418)))",
                "Polygon ((3569754.19176710862666368 6347791.75986070372164249, 3569766.8547038221731782 6347791.60820650681853294, 3569761.38758785324171185 6347785.90534947626292706, 3569754.22482015285640955 6347786.49494275636970997, 3569754.19176710862666368 6347791.75986070372164249))",
                "MultiPolygon (((3569729.18042284436523914 6347796.32892546802759171, 3569724.50720768235623837 6347808.09897327050566673, 3569731.86016463674604893 6347805.21003586146980524, 3569734.03756839968264103 6347798.36081881076097488, 3569729.18042284436523914 6347796.32892546802759171)))",
                "MultiPolygon (((3569722.45611009420827031 6347771.28532140143215656, 3569710.86980802612379193 6347766.17351451888680458, 3569713.48065453907474875 6347773.62974787130951881, 3569720.24329600436612964 6347776.06275871675461531, 3569722.45611009420827031 6347771.28532140143215656)))",
                "MultiPolygon (((3569753.39613456837832928 6347782.79288418311625719, 3569761.50192580418661237 6347782.53140704613178968, 3569752.61170315882191062 6347779.65515854395925999, 3569753.39613456837832928 6347782.79288418311625719)))",
                "MultiPolygon (((3569753.13465743185952306 6347770.89567446615546942, 3569752.08874888531863689 6347773.379707264713943, 3569762.15561864571645856 6347768.15016453247517347, 3569753.13465743185952306 6347770.89567446615546942)))",
                "MultiPolygon (((3569738.04293423052877188 6347795.70041574910283089, 3569737.29699251614511013 6347803.77604531031101942, 3569741.25372670777142048 6347795.31122879404574633, 3569738.04293423052877188 6347795.70041574910283089)))",
                "MultiPolygon (((3569739.92251957906410098 6347764.54570444952696562, 3569739.96497977105900645 6347756.43580808863043785, 3569736.75760231213644147 6347765.212002819404006, 3569739.92251957906410098 6347764.54570444952696562)))",
                "MultiPolygon (((3569722.41109387902542949 6347780.70106708910316229, 3569714.3053026432171464 6347780.9625442260876298, 3569723.19552528858184814 6347783.83879272826015949, 3569722.41109387902542949 6347780.70106708910316229)))",
                "MultiPolygon (((3569729.28231467353180051 6347765.00057455152273178, 3569731.90566611709073186 6347765.61893596407026052, 3569725.07520849397405982 6347756.56162771955132484, 3569729.28231467353180051 6347765.00057455152273178)))",
                "MultiPolygon (((3569723.18460257723927498 6347791.01382320839911699, 3569723.619303940795362 6347788.3538648709654808, 3569715.0581711046397686 6347795.79678019601851702, 3569723.18460257723927498 6347791.01382320839911699)))",
                "MultiPolygon (((3569747.66514745121821761 6347795.68019161652773619, 3569745.13767131650820374 6347794.74413178022950888, 3569750.80329665401950479 6347804.57218720857053995, 3569747.66514745121821761 6347795.68019161652773619)))",
            ],
            [1, 0, 1, *[0 for _ in range(len(POLYGONS) - 3)]],
            0.0,
            89.9,
            False,
            True,
        ),
    ],
    ids=["standard", "by_longest", "distance_angle", "no_multi"],
)
def test_pptl(
    lines, polys, expected, _rotated, distance, angle, longest, no_multi, qgis_processing, add_features, converter
):
    # pydevd_pycharm.settrace("host.docker.internal", port=53100, stdoutToServer=True, stderrToServer=True)
    line_layer = QgsVectorLayer("linestring", "temp_line", "memory")
    add_features(line_layer, lines)

    poly_layer = QgsVectorLayer("polygon", "temp_poly", "memory")
    add_features(poly_layer, polys)

    params = {
        "LINE_LAYER": line_layer,
        "POLYGON_LAYER": poly_layer,
        "LONGEST": longest,
        "NO_MULTI": no_multi,
        "DISTANCE": distance,
        "ANGLE": angle,
        "OUTPUT": QgsProcessingOutputLayerDefinition("TEMPORARY_OUTPUT"),
    }
    result = processing.run(Algorithm(), params)

    for res, exp in zip(result["result_wkt"], expected):
        assert QgsGeometry.compare(converter(res), converter(exp), 0.0000001)

    assert result["_rotated"] == _rotated


@pytest.fixture(scope="session")
def add_features():
    def wrapped(vlayer, wkts):
        pr = vlayer.dataProvider()
        for wkt in wkts:
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(wkt))
            pr.addFeature(f)

    return wrapped


@pytest.fixture(scope="session")
def converter():
    def wrapped(x):
        geom = QgsGeometry.fromWkt(x)
        if geom.isMultipart():
            return geom.asMultiPolygon()
        return geom.asPolygon()

    return wrapped

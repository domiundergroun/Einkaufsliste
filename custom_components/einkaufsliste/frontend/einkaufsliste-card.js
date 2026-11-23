/*
 * Einkaufsliste-Karte für Home Assistant
 * Zeigt eine Bring!-Liste (Integration „einkaufsliste“) als hübsche Kacheln an –
 * mit Reitern für Geschäfte.
 * https://github.com/domiundergroun/Einkaufsliste
 */
const CARD_VERSION = "1.2.0";

const ACCENTS = {
  bring: ["#ee524f", "#d63d3a"],
  smaragd: ["#1fae7a", "#13895e"],
  ozean: ["#2f80ed", "#1c5fc0"],
  violett: ["#8b5cf6", "#6d3fe0"],
  orange: ["#f2994a", "#e07b22"],
  graphit: ["#4b5563", "#2f3742"],
  theme: ["var(--primary-color)", "var(--primary-color)"],
};

function foldKey(s) {
  return String(s ?? "")
    .toLowerCase()
    .replace(/ä/g, "ae").replace(/ö/g, "oe").replace(/ü/g, "ue").replace(/ß/g, "ss")
    .replace(/[éèê]/g, "e").replace(/[áàâ]/g, "a").replace(/[ç]/g, "c")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

// Emoji → Stichwörter (deutsch). Zusammengesetzte Wörter werden über die Endung erkannt
// (z. B. „Vollkornbrot“ → brot, „Bergkäse“ → käse).
const EMOJI_CATALOG = [
  ["🥛", "milch,haferdrink,sojadrink,mandeldrink,reisdrink,pflanzendrink,barista,vollmilch,frischmilch,h-milch,hafermilch,sojamilch,mandelmilch,reismilch,buttermilch,sahne,schlagsahne,kaffeesahne,kondensmilch,kaffeeweißer,milchdrink"],
  ["🧀", "käse,gouda,emmentaler,edamer,parmesan,mozzarella,feta,camembert,brie,frischkäse,hüttenkäse,bergkäse,cheddar,raclette,halloumi,mascarpone,ricotta,schafskäse,reibekäse,tilsiter,butterkäse,scheibenkäse,grana padano,gorgonzola,leerdammer,appenzeller,hirtenkäse,streichkäse,ziegenkäse,pecorino"],
  ["🧈", "butter,margarine,kräuterbutter,süßrahmbutter,ghee,butterschmalz,schmalz"],
  ["🥚", "ei,eier,wachteleier,bio-eier"],
  ["🥣", "joghurt,naturjoghurt,quark,magerquark,skyr,müsli,cornflakes,haferflocken,porridge,granola,kefir,ayran,frühstücksflocken,cerealien,schmand,saure sahne,crème fraîche,creme fraiche,dickmilch"],
  ["🍮", "pudding,grießpudding,dessert,götterspeise,mousse,tiramisu,panna cotta,milchschnitte"],
  ["🍞", "brot,toast,toastbrot,vollkornbrot,mischbrot,sauerteigbrot,knäckebrot,sandwich,sandwichtoast,weißbrot,roggenbrot,graubrot,dinkelbrot,pumpernickel,zwieback"],
  ["🥖", "baguette,brötchen,semmel,semmeln,ciabatta,laugenstange,aufbackbrötchen,schrippe,weckle,baguettebrötchen,kaiserbrötchen"],
  ["🥐", "croissant,croissants,hörnchen,gebäck,plunder,teilchen,franzbrötchen,schnecke,brioche"],
  ["🥨", "brezel,brezeln,breze,laugenbrezel,salzstangen,salzbrezeln"],
  ["🥯", "bagel,bagels"],
  ["🫓", "fladenbrot,pita,naan,wraps,tortilla,tortillas,lavash,yufka"],
  ["🧇", "waffel,waffeln"],
  ["🥞", "pfannkuchen,pancakes,crêpes,crepes,eierkuchen"],
  ["🍰", "kuchen,torte,käsekuchen,obstkuchen,marmorkuchen,tortenboden"],
  ["🧁", "muffin,muffins,cupcakes,muffinförmchen"],
  ["🍪", "keks,kekse,cookies,plätzchen,butterkekse,löffelbiskuit,löffelbiskuits,leibniz,oreo,lebkuchen,spekulatius,printen"],
  ["🍫", "schokolade,schoko,kakao,kakaopulver,schokoriegel,kuvertüre,schokotropfen,pralinen,überraschungsei,nougat,milka,ritter sport"],
  ["🍬", "bonbons,gummibärchen,süßigkeiten,fruchtgummi,lakritz,kaugummi,marshmallows,weingummi,haribo"],
  ["🍭", "lutscher,lolli"],
  ["🧂", "salz,meersalz,jodsalz,pfeffer,gewürze,gewürz,paprikapulver,curry,currypulver,zimt,muskat,oregano,brühwürfel,kümmel,chiliflocken,gewürzmischung,kurkuma,cayennepfeffer,vanille,nelken,lorbeer"],
  ["🍚", "reis,basmati,basmatireis,jasminreis,risottoreis,milchreis,langkornreis,wildreis,sushireis,parboiled"],
  ["🍝", "nudeln,pasta,spaghetti,penne,fusilli,farfalle,tagliatelle,lasagne,lasagneplatten,makkaroni,tortellini,ravioli,gnocchi,spätzle,bandnudeln,eiernudeln,suppennudeln,rigatoni,linguine,maccheroni"],
  ["🍜", "ramen,instantnudeln,mie-nudeln,glasnudeln,reisnudeln,suppe,brühe,gemüsebrühe,hühnerbrühe,rinderbrühe,fond,eintopf,tütensuppe"],
  ["🌾", "mehl,weizenmehl,dinkelmehl,roggenmehl,vollkornmehl,grieß,couscous,bulgur,quinoa,hirse,polenta,hefe,trockenhefe,backpulver,natron,paniermehl,semmelbrösel,speisestärke,stärke,gelatine,haferkleie,leinsamen,chiasamen"],
  ["🍬", "zucker,puderzucker,vanillezucker,rohrzucker,brauner zucker,gelierzucker,süßstoff,xylit,würfelzucker"],
  ["🍯", "honig,marmelade,konfitüre,nutella,aufstrich,nussnougatcreme,sirup,ahornsirup,agavendicksaft,gelee,apfelmus,zuckerrübensirup"],
  ["🥜", "erdnüsse,erdnuss,nüsse,walnüsse,haselnüsse,cashews,cashewkerne,erdnussbutter,pistazien,studentenfutter,macadamia,pekannüsse,paranüsse,nussmischung"],
  ["🌰", "maronen,kastanien,mandeln,gemahlene mandeln,mandelblättchen"],
  ["🍎", "apfel,äpfel,boskop,elstar,pink lady,braeburn,gala"],
  ["🍏", "grüner apfel,granny smith"],
  ["🍐", "birne,birnen"],
  ["🍊", "orange,orangen,mandarine,mandarinen,clementine,clementinen,grapefruit,blutorangen"],
  ["🍋", "zitrone,zitronen,limette,limetten,zitronensaft,limettensaft"],
  ["🍌", "banane,bananen"],
  ["🍉", "wassermelone,melone"],
  ["🍈", "honigmelone,cantaloupe,galiamelone"],
  ["🍇", "trauben,weintrauben,rosinen"],
  ["🍓", "erdbeere,erdbeeren"],
  ["🫐", "heidelbeeren,blaubeeren,beeren,himbeeren,brombeeren,johannisbeeren,cranberrys,cranberries,stachelbeeren,beerenmischung"],
  ["🍒", "kirsche,kirschen,sauerkirschen"],
  ["🍑", "pfirsich,pfirsiche,nektarine,nektarinen,aprikose,aprikosen,pflaumen,zwetschgen,mirabellen"],
  ["🥭", "mango,mangos,papaya,maracuja,passionsfrucht"],
  ["🍍", "ananas"],
  ["🥥", "kokosnuss,kokos,kokosmilch,kokosraspeln,kokosöl"],
  ["🥝", "kiwi,kiwis"],
  ["🍅", "tomate,tomaten,cherrytomaten,cocktailtomaten,rispentomaten,passierte tomaten,tomatenmark,dosentomaten,stückige tomaten,getrocknete tomaten,tomatensoße,tomatensauce"],
  ["🍆", "aubergine,auberginen"],
  ["🥑", "avocado,avocados,guacamole"],
  ["🫛", "erbsen,zuckerschoten,edamame,erbsen und möhren"],
  ["🥦", "brokkoli,broccoli,blumenkohl,romanesco,rosenkohl,kohlrabi"],
  ["🥬", "salat,eisbergsalat,kopfsalat,rucola,spinat,blattspinat,mangold,chinakohl,kohl,weißkohl,rotkohl,wirsing,grünkohl,feldsalat,lauch,porree,römersalat,pak choi,sauerkraut,lollo rosso,radicchio,endivie"],
  ["🥒", "gurke,gurken,salatgurke,zucchini,essiggurken,gewürzgurken,cornichons,minigurken"],
  ["🌶️", "chili,chilis,peperoni,jalapeños,jalapenos,peperoncini,sambal,sriracha,tabasco"],
  ["🫑", "paprika,paprikaschoten,spitzpaprika"],
  ["🌽", "mais,maiskolben,zuckermais"],
  ["🥕", "karotte,karotten,möhre,möhren,rüebli,pastinaken,petersilienwurzel,rote bete,rote beete,radieschen,rettich,sellerie,knollensellerie,staudensellerie,fenchel,spargel"],
  ["🫒", "oliven,olivenöl,öl,rapsöl,sonnenblumenöl,speiseöl,bratöl,sesamöl,leinöl,kapern"],
  ["🧄", "knoblauch,knoblauchzehen,knofi"],
  ["🧅", "zwiebel,zwiebeln,rote zwiebeln,schalotten,frühlingszwiebeln,lauchzwiebeln,röstzwiebeln,gemüsezwiebel"],
  ["🥔", "kartoffel,kartoffeln,festkochende kartoffeln,mehligkochende kartoffeln,pommes,pommes frites,kroketten,kartoffelpüree,rösti,kartoffelpuffer,bratkartoffeln,kartoffelsalat,gnocchi"],
  ["🍠", "süßkartoffel,süßkartoffeln"],
  ["🫚", "ingwer,kurkumawurzel"],
  ["🍄", "pilze,champignons,pfifferlinge,steinpilze,austernpilze,shiitake,kräuterseitlinge"],
  ["🫘", "bohnen,grüne bohnen,kidneybohnen,weiße bohnen,linsen,rote linsen,kichererbsen,baked beans,sojabohnen,tofu,tempeh"],
  ["🌿", "kräuter,petersilie,basilikum,schnittlauch,dill,koriander,minze,rosmarin,thymian,salbei,kresse,pesto,kräuter der provence,bärlauch"],
  ["🥗", "salatmischung,salatbox,krautsalat,nudelsalat,salatdressing,dressing"],
  ["🍕", "pizza,tiefkühlpizza,pizzateig,flammkuchen,flammkuchenteig,baguette pizza"],
  ["🌮", "tacos,taco,taco shells,nachos,burritos,enchiladas"],
  ["🍔", "burger,burgerbrötchen,burger patties,patties,hamburger,cheeseburger"],
  ["🌭", "wurst,würstchen,wiener,wienerle,frankfurter,bratwurst,bockwurst,currywurst,salami,aufschnitt,leberwurst,mortadella,chorizo,mettwurst,lyoner,fleischwurst,teewurst,leberkäse,hot dog,weißwurst,cabanossi,landjäger"],
  ["🥓", "speck,schinken,bacon,kochschinken,schinkenwürfel,parmaschinken,serranoschinken,katenschinken,lachsschinken,bacon streifen,putenschinken"],
  ["🥩", "fleisch,steak,steaks,rindfleisch,schweinefleisch,hackfleisch,hack,gulasch,schnitzel,braten,lamm,lammfleisch,kotelett,rinderhack,gemischtes hack,rinderfilet,filet,rouladen,geschnetzeltes,schweinebauch,spareribs,ribs,minutensteaks,kalbfleisch,wild,frikadellen,cevapcici,hackbällchen,mett"],
  ["🍗", "hähnchen,hühnchen,huhn,hähnchenbrust,hühnerbrust,chicken,chicken wings,chicken nuggets,nuggets,pute,putenbrust,putenfleisch,putenschnitzel,hähnchenschenkel,hähnchenkeulen,ente,entenbrust,geflügel,hühnerfrikassee,gans"],
  ["🐟", "fisch,lachs,lachsfilet,räucherlachs,thunfisch,forelle,kabeljau,seelachs,hering,matjes,makrele,fischstäbchen,sardinen,dorade,pangasius,zander,rotbarsch,scholle,fischfilet,rollmops,backfisch"],
  ["🦐", "garnelen,shrimps,krabben,scampi,gambas,meeresfrüchte,muscheln,miesmuscheln,hummer"],
  ["🦑", "tintenfisch,calamari,oktopus,tintenfischringe"],
  ["🍣", "sushi,nori,noriblätter,wasabi"],
  ["🥟", "maultaschen,dumplings,teigtaschen,piroggen,pelmeni,gyoza,frühlingsrollen,samosas,empanadas"],
  ["🧆", "falafel,hummus,humus,tahini"],
  ["🥙", "döner,gyros,kebab,dürüm,gyrosfleisch"],
  ["🥧", "quiche,blätterteig,mürbeteig,pizzateig,strudelteig,yufkateig,filoteig,pastete,tarte"],
  ["🍳", "pfanne,bratfett,rührei,spiegelei"],
  ["🥫", "dose,dosen,konserve,konserven,ketchup,senf,mayonnaise,mayo,remoulade,soße,sauce,bbq sauce,grillsoße,currysoße,hollandaise,bratensoße,soßenbinder,ravioli dose,eintopf dose,dosenmais,dosenbohnen,kidneybohnen dose,tomatenketchup,aioli,tzatziki,salsa"],
  ["🍶", "essig,balsamico,weißweinessig,apfelessig,sojasauce,sojasoße,worcestersauce,fischsauce,teriyaki,hoisin,austernsauce"],
  ["☕", "kaffee,kaffeebohnen,espresso,kaffeepads,kaffeekapseln,kapseln,cappuccino,instantkaffee,filterkaffee,kaffeepulver,latte macchiato,cold brew,kaffeefilter,filtertüten"],
  ["🍵", "tee,jasmintee,earl grey,ostfriesentee,hagebuttentee,salbeitee,brennnesseltee,yogi tee,grüner tee,schwarzer tee,früchtetee,kräutertee,pfefferminztee,kamillentee,rooibos,matcha,chai,teebeutel,fencheltee,ingwertee,mate"],
  ["🧋", "eistee,eiskaffee,bubble tea,ice tea"],
  ["🧃", "saft,orangensaft,o-saft,apfelsaft,multivitaminsaft,traubensaft,smoothie,smoothies,apfelschorle,schorle,saftschorle,direktsaft,nektar,kirschsaft,maracujasaft,ananassaft,tomatensaft,karottensaft,capri-sun,capri sun"],
  ["🥤", "cola,cola zero,coca-cola,coca cola,pepsi,limo,limonade,fanta,sprite,spezi,mezzo mix,energydrink,energy drink,red bull,monster,club mate,mate tee,fassbrause,bionade,tonic,tonic water,ginger ale,bitter lemon,eistee pulver,sirupwasser,sodastream"],
  ["💧", "wasser,mineralwasser,sprudel,sprudelwasser,stilles wasser,medium,heilwasser,wasserkisten,kisten wasser"],
  ["🍺", "bier,pils,pilsner,weizen,weizenbier,weißbier,radler,alster,alkoholfreies bier,helles,export,kölsch,alt,altbier,craft beer,ipa,dunkles,bockbier,cider"],
  ["🍷", "wein,rotwein,weißwein,rosé,rose,roséwein,glühwein,sangria,merlot,riesling,dornfelder,grauburgunder,chardonnay,lambrusco"],
  ["🍾", "sekt,prosecco,champagner,crémant,cremant,secco,hugo,aperol,spritz"],
  ["🥃", "whisky,whiskey,schnaps,rum,wodka,vodka,gin,likör,korn,ouzo,tequila,jägermeister,amaretto,eierlikör,obstler,cognac,weinbrand,baileys,limoncello,mezcal,grappa"],
  ["🧊", "eiswürfel,crushed ice,crushed eis,eis würfel"],
  ["🍨", "eis,erdbeereis,schokoladeneis,schokoeis,zitroneneis,mangoeis,joghurteis,nusseis,stracciatellaeis,himbeereis,kirscheis,bananeneis,kokoseis,karamelleis,eiscreme,speiseeis,vanilleeis,schokoeis,stieleis,eis am stiel,sorbet,frozen yoghurt,magnum,cornetto,eiskonfekt"],
  ["🍿", "popcorn,chips,kartoffelchips,tortillachips,snacks,flips,erdnussflips,cracker,salzcracker,knabberzeug,pringles,crunchips,reiswaffeln,brezeln snack"],
  ["🥤", "trinkhalme,strohhalme,becher,pappbecher"],
  ["🧻", "klopapier,toilettenpapier,küchenrolle,küchenpapier,küchentücher,servietten,feuchtes toilettenpapier,zewa,papiertücher"],
  ["🤧", "taschentücher,tempo,kosmetiktücher"],
  ["🧼", "seife,handseife,flüssigseife,seifenspender,nachfüllseife,kernseife,desinfektionsmittel,handdesinfektion"],
  ["🧴", "shampoo,duschgel,duschbad,spülung,haarspülung,conditioner,bodylotion,lotion,creme,gesichtscreme,sonnencreme,sonnenmilch,handcreme,deo,deodorant,deospray,haarspray,haargel,haarschaum,gesichtswasser,abschminktücher,abschminkpads,wattepads,wattestäbchen,nivea,babyöl,lippenpflege,labello,trockenshampoo,haaröl,bodyspray,parfum,parfüm,rasiergel,aftershave"],
  ["🪥", "zahnbürste,zahnbürsten,zahnpasta,zahncreme,zahnseide,mundspülung,mundwasser,interdentalbürsten,aufsteckbürsten,zahnbürstenköpfe"],
  ["🪒", "rasierer,rasierklingen,einwegrasierer,rasierschaum,rasierhobel,klingen"],
  ["💄", "make-up,makeup,lippenstift,mascara,nagellack,nagellackentferner,puder,concealer,foundation,kajal,eyeliner,lidschatten"],
  ["🩲", "unterwäsche,unterhosen,slips"],
  ["🧦", "socken,strumpfhose,strumpfhosen"],
  ["🧽", "schwamm,schwämme,spülmittel,spüli,spülschwamm,putzmittel,allzweckreiniger,reiniger,glasreiniger,badreiniger,wc-reiniger,klostein,wc-steine,scheuermilch,essigreiniger,entkalker,backofenreiniger,fettlöser,putzlappen,putztücher,mikrofasertücher,stahlwolle,bodenreiniger,kalkreiniger,abflussreiniger,rohrreiniger,feuchttücher reinigung,schmierseife,spültücher,spüllappen"],
  ["🧺", "waschmittel,weichspüler,waschpulver,colorwaschmittel,vollwaschmittel,feinwaschmittel,wollwaschmittel,flüssigwaschmittel,waschmittelpods,fleckentferner,gallseife,hygienespüler,wäscheklammern,farbfangtücher,entkalker waschmaschine,wäschenetz,trocknertücher"],
  ["🍽️", "spülmaschinentabs,geschirrspültabs,geschirrspülmittel,klarspüler,spülmaschinensalz,regeneriersalz,maschinenpfleger,tabs,pappteller,einweggeschirr,plastikbesteck"],
  ["🗑️", "müllbeutel,müllsäcke,mülltüten,gelbe säcke,biobeutel,biomüllbeutel,müllbeutel 35l,müllbeutel 60l"],
  ["🧤", "handschuhe,gummihandschuhe,einweghandschuhe,haushaltshandschuhe,gartenhandschuhe"],
  ["🔋", "batterien,batterie,akkus,aa batterien,aaa batterien,knopfzellen,ladekabel,powerbank"],
  ["💡", "glühbirne,glühbirnen,leuchtmittel,led lampe,led-lampe,led birne"],
  ["🕯️", "kerzen,kerze,teelichter,teelicht,duftkerze,grablicht,stumpenkerzen"],
  ["🔥", "grillkohle,briketts,anzünder,grillanzünder,streichhölzer,feuerzeug,kaminholz,brennholz"],
  ["🪣", "eimer,putzeimer"],
  ["🧹", "besen,kehrblech,wischmopp,mopp,wischbezug,staubsaugerbeutel,staubwedel,swiffer"],
  ["📦", "frischhaltefolie,alufolie,backpapier,gefrierbeutel,gefrierdosen,zipbeutel,brotdose,butterbrotpapier,frühstücksbeutel,klebeband,paketband,kartons,vorratsdosen,muffinförmchen papier"],
  ["💊", "medikamente,tabletten,ibuprofen,paracetamol,aspirin,vitamine,vitamin d,magnesium,nasenspray,hustensaft,halstabletten,lutschtabletten,kopfschmerztabletten,nahrungsergänzung,zink,elektrolyte,thermometer"],
  ["🩹", "pflaster,verband,mullbinden,wundsalbe,desinfektionsspray,blasenpflaster"],
  ["👶", "windeln,feuchttücher,babybrei,babynahrung,gläschen,quetschies,schnuller,babyshampoo,wundschutzcreme,schwimmwindeln,pre-milch,folgemilch,babymilch"],
  ["🍼", "fläschchen,babyflasche,sauger"],
  ["🐱", "katzenfutter,katzenstreu,katzensnacks,nassfutter katze,trockenfutter katze,katzenmilch,kratzbaum"],
  ["🐶", "hundefutter,hundesnacks,kauknochen,leckerli,hundekotbeutel,trockenfutter hund,nassfutter hund"],
  ["🐦", "vogelfutter,meisenknödel,vogelsand"],
  ["🐠", "fischfutter"],
  ["🐹", "nagerfutter,heu,einstreu,kaninchenfutter"],
  ["💐", "blumen,blumenstrauß,strauß,tulpen,rosen,schnittblumen"],
  ["🌱", "blumenerde,erde,pflanzen,saatgut,samen,dünger,kräutertopf,pflanzerde"],
  ["🎁", "geschenk,geschenke,geschenkpapier,geschenkband,geburtstagskarte,karte,glückwunschkarte"],
  ["✉️", "briefmarken,briefumschläge,umschläge,briefpapier"],
  ["✏️", "stifte,kugelschreiber,bleistifte,radiergummi,textmarker,schreibblock,collegeblock,hefte,notizblock,druckerpapier,druckerpatronen,toner,ordner,klebestift"],
  ["🧯", "rauchmelder,feuerlöscher"],
  ["🔩", "schrauben,dübel,nägel,werkzeug,kabelbinder,sekundenkleber,kleber,wd-40,silikon"],
  ["🧷", "sicherheitsnadeln,nähzeug,knöpfe,nähgarn"],
  ["🧩", "spielzeug,puzzle,spiel,spiele,bastelsachen"],
  ["🎈", "luftballons,partydeko,deko,servietten party,konfetti,girlande"],
  ["🚬", "zigaretten,tabak,blättchen,filter"],
  ["🧃", "trinkpäckchen"],
  ["🥜", "erdnüsse"],
  ["🍙", "reisbällchen,onigiri"],
  ["🍡", "mochi"],
  ["🥠", "glückskekse"],
  ["🫕", "fondue,fonduekäse"],
  ["🥘", "paella,fertiggericht,fertiggerichte,tiefkühlgericht,auflauf,chili con carne,curry fertig"],
  ["🍛", "currypaste,kokos curry,dal"],
  ["🥮", "mondkuchen"],
  ["🍩", "donut,donuts,berliner,krapfen,pfannkuchen gebäck"],
  ["🎂", "geburtstagskuchen,kerzen geburtstag,tortenkerzen"],
  ["🍦", "softeis,waffeleis,eishörnchen,eiswaffeln"],
  ["🥡", "takeaway,essen zum mitnehmen,asianudeln box"],
];

const EMOJI_INDEX = (() => {
  const map = new Map();
  for (const [emoji, words] of EMOJI_CATALOG) {
    for (const w of words.split(",")) {
      const k = foldKey(w);
      if (k && !map.has(k)) map.set(k, emoji);
    }
  }
  return map;
})();

const emojiCache = new Map();

function emojiFor(name) {
  const k = foldKey(name);
  if (emojiCache.has(k)) return emojiCache.get(k);
  let result = EMOJI_INDEX.get(k) || null;
  if (!result) {
    const words = k.split(" ").filter(Boolean);
    // 1) ein Wort passt genau („Bio Eier“ → eier)
    for (const w of words) {
      if (EMOJI_INDEX.has(w)) { result = EMOJI_INDEX.get(w); break; }
    }
    // 2) zusammengesetzte Wörter über die Endung („Vollkornbrot“ → brot), längster Treffer gewinnt
    if (!result) {
      let best = "";
      for (const key of EMOJI_INDEX.keys()) {
        if (key.length < 4 || key.length <= best.length) continue;
        if (k.endsWith(key) || words.some((w) => w.endsWith(key))) best = key;
      }
      // 3) irgendwo enthalten („Tomatenmark klein“ …)
      if (!best) {
        for (const key of EMOJI_INDEX.keys()) {
          if (key.length >= 5 && key.length > best.length && k.includes(key)) best = key;
        }
      }
      if (best) result = EMOJI_INDEX.get(best);
      else if (/tee$/.test(words[words.length - 1] || "")) result = "🍵";
    }
  }
  emojiCache.set(k, result);
  return result;
}

const failedImages = new Set();
const failedLogos = new Set();

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

const slugify = (name) => foldKey(name).replace(/ /g, "_");

function hueFor(name) {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return h;
}

function fallbackIcon(name) {
  const emoji = emojiFor(name);
  if (emoji) return `<span class="emoji">${emoji}</span>`;
  const letter = esc((name.trim()[0] || "?").toUpperCase());
  return `<span class="letter" style="--h:${hueFor(name)}">${letter}</span>`;
}

function iconHtml(name, useImages) {
  const slug = slugify(name);
  if (useImages && slug && !failedImages.has(slug)) {
    return `<img loading="lazy" alt="" data-slug="${slug}" src="https://web.getbring.com/assets/images/items/${slug}.png">`;
  }
  return fallbackIcon(name);
}

function storeLogo(store, cls = "slogo") {
  if (!store) return `<span class="${cls} semoji">🛒</span>`;
  if (store.domain) {
    return `<img class="${cls}" alt="" data-letter="${esc((store.name || "?").trim()[0].toUpperCase())}" data-hue="${hueFor(store.name || "")}" data-cls="${cls}"
      src="https://www.google.com/s2/favicons?domain=${encodeURIComponent(store.domain)}&sz=128">`;
  }
  return `<span class="${cls} semoji">${esc(store.emoji || "🏪")}</span>`;
}

const ICONS = {
  cart: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M17 18a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2c0-1.11.89-2 2-2M1 2h3.27l.94 2H20a1 1 0 0 1 1 1c0 .17-.05.34-.12.5l-3.58 6.47c-.34.61-1 1.03-1.75 1.03H8.1l-.9 1.63-.03.12a.25.25 0 0 0 .25.25H19v2H7a2 2 0 0 1-2-2c0-.35.09-.68.24-.96l1.36-2.45L3 4H1V2m6 16a2 2 0 0 1 2 2 2 2 0 0 1-2 2 2 2 0 0 1-2-2c0-1.11.89-2 2-2Z"/></svg>`,
  refresh: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M17.65 6.35A7.958 7.958 0 0 0 12 4a8 8 0 0 0-8 8 8 8 0 0 0 8 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0 1 12 18a6 6 0 0 1-6-6 6 6 0 0 1 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35Z"/></svg>`,
  plus: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2Z"/></svg>`,
  check: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17Z"/></svg>`,
  chevron: `<svg viewBox="0 0 24 24"><path fill="currentColor" d="M7.41 8.58 12 13.17l4.59-4.59L18 10l-6 6-6-6 1.41-1.42Z"/></svg>`,
  party: `<svg viewBox="0 0 64 64"><circle cx="32" cy="32" r="30" fill="var(--acc)" opacity=".12"/><path d="M20 33l8 8 16-17" fill="none" stroke="var(--acc)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
};

const STYLE = `
:host { --acc: ${ACCENTS.bring[0]}; --acc2: ${ACCENTS.bring[1]}; }
ha-card { position: relative; overflow: hidden; border-radius: var(--ha-card-border-radius, 20px); }
.wrap { padding: 18px 18px 16px; }
header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.badge { width: 44px; height: 44px; border-radius: 14px; display: grid; place-items: center; color: #fff;
  background: linear-gradient(135deg, var(--acc), var(--acc2)); box-shadow: 0 6px 16px -6px var(--acc); flex: none; }
.badge svg { width: 24px; height: 24px; }
.titles { flex: 1; min-width: 0; }
.title { font-size: 1.25rem; font-weight: 700; letter-spacing: -0.01em; color: var(--primary-text-color);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sub { font-size: 0.85rem; color: var(--secondary-text-color); margin-top: 1px; }
.sub b { color: var(--acc); font-weight: 600; }
.icon-btn { border: 0; background: transparent; color: var(--secondary-text-color); width: 38px; height: 38px;
  border-radius: 12px; display: grid; place-items: center; cursor: pointer; transition: background .2s, color .2s; }
.icon-btn:hover { background: var(--secondary-background-color); color: var(--primary-text-color); }
.icon-btn svg { width: 22px; height: 22px; }
.icon-btn.spin svg { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

form.add { display: flex; gap: 8px; align-items: center; background: var(--secondary-background-color);
  border-radius: 16px; padding: 5px 5px 5px 14px; border: 1.5px solid transparent; transition: border-color .2s, box-shadow .2s; }
form.add:focus-within { border-color: var(--acc); box-shadow: 0 0 0 4px color-mix(in srgb, var(--acc) 15%, transparent); }
form.add input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; font: inherit; font-size: 0.98rem;
  color: var(--primary-text-color); padding: 8px 0; }
form.add input::placeholder { color: var(--secondary-text-color); opacity: .8; }
.add-btn { border: 0; width: 38px; height: 38px; border-radius: 12px; color: #fff; cursor: pointer; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--acc), var(--acc2)); transition: transform .15s, opacity .2s; flex: none; }
.add-btn:active { transform: scale(.92); }
.add-btn svg { width: 22px; height: 22px; }
.suggest { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.suggest:empty { display: none; }
.chip { border: 0; cursor: pointer; font: inherit; font-size: .82rem; padding: 5px 11px; border-radius: 999px;
  background: color-mix(in srgb, var(--acc) 12%, transparent); color: var(--acc); font-weight: 600; }
.chip:hover { background: color-mix(in srgb, var(--acc) 20%, transparent); }

.items { margin-top: 14px; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(var(--tile, 92px), 1fr)); gap: 10px; }
.tile { position: relative; border: 0; cursor: pointer; font: inherit; color: #fff; text-align: center;
  aspect-ratio: 1 / 1; border-radius: 18px; padding: 8px 6px; display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 3px; background: linear-gradient(150deg, var(--acc), var(--acc2));
  box-shadow: 0 6px 14px -8px var(--acc); transition: transform .18s ease, box-shadow .18s ease, opacity .3s;
  -webkit-tap-highlight-color: transparent; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; }
.tile.new, .row.new { animation: pop .28s ease both; }
.tile:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -10px var(--acc); }
.tile:active { transform: scale(.95); }
@keyframes pop { from { transform: scale(.85); opacity: 0; } to { transform: none; opacity: 1; } }
.ico { width: 46px; height: 46px; display: grid; place-items: center; flex: none; }
.ico img { width: 46px; height: 46px; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(0,0,0,.18)); }
.emoji { font-size: 30px; line-height: 1; filter: drop-shadow(0 2px 3px rgba(0,0,0,.15)); }
.letter { width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center; font-weight: 700; font-size: 1.1rem;
  background: rgba(255,255,255,.22); color: #fff; }
.name { font-size: .84rem; font-weight: 600; line-height: 1.15; max-width: 100%; overflow: hidden; text-overflow: ellipsis;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow-wrap: anywhere; hyphens: auto; }
.spec { font-size: .72rem; opacity: .85; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tile.done { pointer-events: none; animation: done .45s ease forwards; }
.tile .tick { position: absolute; inset: 0; display: grid; place-items: center; border-radius: inherit;
  background: rgba(0,0,0,.25); opacity: 0; transition: opacity .15s; }
.tile .tick svg { width: 40px; height: 40px; color: #fff; }
.tile.done .tick { opacity: 1; }
@keyframes done { 0% { transform: scale(1); } 40% { transform: scale(1.06); } 100% { transform: scale(.6); opacity: 0; } }

.list { display: flex; flex-direction: column; gap: 6px; }
.row { display: flex; align-items: center; gap: 12px; border: 0; cursor: pointer; font: inherit; text-align: left; width: 100%;
  padding: 8px 12px 8px 8px; border-radius: 14px; background: var(--secondary-background-color); color: var(--primary-text-color);
  transition: transform .15s, opacity .3s; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; }
.row:active { transform: scale(.98); }
.row .ico { width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(150deg, var(--acc), var(--acc2)); }
.row .ico img { width: 32px; height: 32px; }
.row .emoji { font-size: 22px; }
.row .letter { width: 40px; height: 40px; font-size: 1rem; background: transparent; }
.row .txt { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.row .name { font-size: .95rem; -webkit-line-clamp: 1; }
.row .spec { color: var(--secondary-text-color); opacity: 1; font-size: .8rem; }
.row .circle { width: 24px; height: 24px; border-radius: 50%; border: 2px solid var(--divider-color); flex: none; display: grid;
  place-items: center; color: transparent; transition: all .2s; }
.row .circle svg { width: 16px; height: 16px; }
.row.done { animation: rowdone .45s ease forwards; pointer-events: none; }
.row.done .circle { background: var(--acc); border-color: var(--acc); color: #fff; }
@keyframes rowdone { 60% { opacity: 1; } 100% { opacity: 0; transform: translateX(30px); } }

.empty { text-align: center; padding: 18px 8px 8px; color: var(--secondary-text-color); }
.empty svg { width: 64px; height: 64px; }
.empty .big { font-size: 1.05rem; font-weight: 700; color: var(--primary-text-color); margin-top: 6px; }
.error { margin-top: 12px; padding: 10px 12px; border-radius: 12px; font-size: .85rem;
  background: color-mix(in srgb, var(--error-color, #db4437) 12%, transparent); color: var(--error-color, #db4437); }

.recent-wrap { margin-top: 16px; border-top: 1px solid var(--divider-color); padding-top: 10px; }
.recent-toggle { display: flex; align-items: center; gap: 8px; width: 100%; border: 0; background: transparent; cursor: pointer;
  font: inherit; color: var(--secondary-text-color); font-size: .85rem; font-weight: 600; padding: 4px 2px; letter-spacing: .02em; text-transform: uppercase; }
.recent-toggle .cnt { background: var(--secondary-background-color); border-radius: 999px; padding: 1px 8px; font-size: .75rem; }
.recent-toggle svg { width: 20px; height: 20px; margin-left: auto; transition: transform .25s; }
.recent-wrap.open .recent-toggle svg { transform: rotate(180deg); }
.recent { display: none; margin-top: 10px; }
.recent-wrap.open .recent { display: grid; }
.recent .tile { background: var(--secondary-background-color); color: var(--primary-text-color); box-shadow: none; --tile: 76px; }
.recent .tile .ico { width: 34px; height: 34px; }
.recent .tile .ico img { width: 34px; height: 34px; filter: grayscale(.35); opacity: .85; }
.recent .tile .emoji { font-size: 22px; }
.recent .tile .letter { width: 30px; height: 30px; background: hsl(var(--h) 55% 55% / .9); font-size: .9rem; }
.recent .tile .name { font-size: .76rem; font-weight: 500; }
.recent .tile .spec { display: none; }
.recent.grid { grid-template-columns: repeat(auto-fill, minmax(76px, 1fr)); gap: 8px; }
.recent .tile:hover { box-shadow: inset 0 0 0 2px var(--acc); }
.recent .tile.readd { animation: done .4s ease forwards; }

.sheet { position: absolute; inset: 0; display: flex; align-items: flex-end; justify-content: center; z-index: 5;
  background: rgba(0,0,0,.35); backdrop-filter: blur(3px); -webkit-backdrop-filter: blur(3px); animation: fade .2s ease; }
.sheet[hidden] { display: none; }
@keyframes fade { from { opacity: 0; } }
.panel { width: 100%; background: var(--ha-card-background, var(--card-background-color, #fff)); border-radius: 20px 20px 0 0;
  padding: 18px; box-shadow: 0 -10px 30px rgba(0,0,0,.2); animation: up .25s ease; }
@keyframes up { from { transform: translateY(40px); opacity: 0; } }
.panel h3 { margin: 0 0 12px; font-size: 1.05rem; color: var(--primary-text-color); }
.panel label { display: block; font-size: .78rem; color: var(--secondary-text-color); margin: 8px 0 4px; font-weight: 600; }
.panel input { width: 100%; box-sizing: border-box; border: 1.5px solid var(--divider-color); border-radius: 12px; padding: 10px 12px;
  font: inherit; background: var(--secondary-background-color); color: var(--primary-text-color); outline: 0; }
.panel input:focus { border-color: var(--acc); }
.actions { display: flex; gap: 8px; margin-top: 16px; }
.actions button { border: 0; border-radius: 12px; padding: 10px 14px; font: inherit; font-weight: 600; cursor: pointer; }
.btn-del { background: color-mix(in srgb, var(--error-color, #db4437) 14%, transparent); color: var(--error-color, #db4437); }
.btn-cancel { margin-left: auto; background: var(--secondary-background-color); color: var(--primary-text-color); }
.btn-save { background: linear-gradient(135deg, var(--acc), var(--acc2)); color: #fff; }

.tabs { display: flex; gap: 8px; overflow-x: auto; margin: 14px -18px 0; padding: 2px 18px 4px; scrollbar-width: none; }
.tabs::-webkit-scrollbar { display: none; }
.tabs[hidden] { display: none; }
.tab { flex: none; display: inline-flex; align-items: center; gap: 7px; border: 0; cursor: pointer; font: inherit;
  font-size: .88rem; font-weight: 600; padding: 7px 12px 7px 8px; border-radius: 999px; white-space: nowrap;
  background: var(--secondary-background-color); color: var(--primary-text-color); transition: background .2s, color .2s, box-shadow .2s; }
.tab .n { font-size: .74rem; padding: 1px 7px; border-radius: 999px; background: color-mix(in srgb, var(--primary-text-color) 10%, transparent); }
.tab.active { background: linear-gradient(135deg, var(--acc), var(--acc2)); color: #fff; box-shadow: 0 6px 14px -8px var(--acc); }
.tab.active .n { background: rgba(255,255,255,.25); }
.tab.icon-tab { position: relative; padding: 5px; width: 46px; height: 40px; justify-content: center; border-radius: 14px; overflow: visible; }
.tab.icon-tab .slogo { width: 28px; height: 28px; border-radius: 8px; font-size: 18px; }
.tab.icon-tab .n { position: absolute; top: -5px; right: -5px; min-width: 18px; height: 18px; box-sizing: border-box; padding: 0 5px;
  display: grid; place-items: center; font-size: .68rem; line-height: 1; background: var(--acc); color: #fff;
  border: 2px solid var(--ha-card-background, var(--card-background-color, #fff)); }
.tab.icon-tab.active { background: color-mix(in srgb, var(--acc) 14%, transparent); box-shadow: inset 0 0 0 2px var(--acc); }
.tab.icon-tab.active .n { background: var(--acc2); }
.tabs { padding-top: 7px; }
.tab.cart-tab .cart-ico { width: 28px; height: 28px; display: grid; place-items: center; color: var(--acc); }
.tab.cart-tab .cart-ico svg { width: 24px; height: 24px; }
.tab.cart-tab.active { background: linear-gradient(135deg, var(--acc), var(--acc2)); box-shadow: 0 6px 14px -8px var(--acc); }
.tab.cart-tab.active .cart-ico { color: #fff; }
.tab.cart-tab.active .n { background: #fff; color: var(--acc); }
.tab.name-tab { position: relative; height: 40px; padding: 0 14px; border-radius: 14px; gap: 6px; overflow: visible;
  background: linear-gradient(135deg, hsl(var(--h) 75% 55% / .16), hsl(calc(var(--h) + 25) 75% 55% / .10));
  box-shadow: inset 0 0 0 1px hsl(var(--h) 60% 50% / .25); color: color-mix(in srgb, hsl(var(--h) 65% 42%) 60%, var(--primary-text-color)); }
.tab.name-tab .nt-name { font-weight: 800; font-size: .86rem; letter-spacing: .01em; }
.tab.name-tab .nt-emoji { font-size: 18px; line-height: 1; }
.tab.name-tab .n { position: absolute; top: -5px; right: -5px; min-width: 18px; height: 18px; box-sizing: border-box; padding: 0 5px;
  display: grid; place-items: center; font-size: .68rem; line-height: 1; background: var(--acc); color: #fff;
  border: 2px solid var(--ha-card-background, var(--card-background-color, #fff)); }
.tab.name-tab.active { background: linear-gradient(135deg, hsl(var(--h) 70% 50%), hsl(calc(var(--h) + 25) 70% 45%)); color: #fff;
  box-shadow: 0 6px 14px -8px hsl(var(--h) 70% 45%); }
.tab.name-tab.active .n { background: #fff; color: hsl(var(--h) 60% 40%); }
.slogo { width: 22px; height: 22px; border-radius: 7px; background: #fff; object-fit: contain; flex: none;
  box-shadow: 0 0 0 1px rgba(0,0,0,.06); display: inline-grid; place-items: center; font-size: 15px; line-height: 1; }
.slogo.semoji { background: transparent; box-shadow: none; }
.slogo.sletter { background: hsl(var(--h) 60% 45%); color: #fff; font-weight: 700; font-size: 12px; box-shadow: none; }
.section { font-size: .78rem; font-weight: 700; letter-spacing: .03em; text-transform: uppercase; color: var(--secondary-text-color);
  margin: 4px 2px 8px; display: flex; align-items: center; gap: 8px; }
.section + .grid, .section + .list { margin-bottom: 14px; }
.section .slogo { width: 18px; height: 18px; border-radius: 5px; font-size: 13px; }
.hint { margin-top: 10px; font-size: .8rem; color: var(--secondary-text-color); text-align: center; }
.tile .badge-store { position: absolute; top: 6px; right: 6px; width: 20px; height: 20px; border-radius: 6px; background: #fff;
  display: grid; place-items: center; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,.2); font-size: 13px; }
.tile .badge-store img, .tile .badge-store .slogo { width: 16px; height: 16px; box-shadow: none; border-radius: 4px; }
.row .badge-store { width: 22px; height: 22px; display: grid; place-items: center; flex: none; }
.row .badge-store .slogo { width: 20px; height: 20px; }
.store-pick { display: flex; flex-wrap: wrap; gap: 6px; }
.store-pick button { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid var(--divider-color); cursor: pointer;
  font: inherit; font-size: .84rem; padding: 5px 10px 5px 6px; border-radius: 999px; background: transparent; color: var(--primary-text-color); }
.store-pick button.sel { border-color: var(--acc); background: color-mix(in srgb, var(--acc) 12%, transparent); color: var(--acc); font-weight: 600; }
.store-pick .slogo { width: 20px; height: 20px; }
.store-empty { font-size: .8rem; color: var(--secondary-text-color); }
/* Abgehakt: grau, durchgestrichen, am Ende – antippen macht es rückgängig */
.tile.checked { background: var(--secondary-background-color); color: var(--secondary-text-color); box-shadow: none; }
.tile.checked:hover { box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--acc) 45%, transparent); transform: none; }
.tile.checked .ico { filter: grayscale(1); opacity: .45; }
.tile.checked .name, .tile.checked .spec { text-decoration: line-through; text-decoration-thickness: 2px; opacity: .75; }
.tile.checked .badge-store { filter: grayscale(1); opacity: .6; }
.tile.checked .tick { opacity: 1; background: transparent; inset: auto; top: 6px; left: 6px; width: 20px; height: 20px;
  border-radius: 50%; background: color-mix(in srgb, var(--secondary-text-color) 55%, transparent); }
.tile.checked .tick svg { width: 14px; height: 14px; }
.tile.checking { animation: none; transform: scale(.94); filter: grayscale(1); opacity: .6; transition: all .25s ease; }
.tile.checking .tick { opacity: 1; }
.tile.unchecking, .row.unchecking { opacity: .3; transform: scale(.96); transition: all .18s ease; }
.row.checked { background: transparent; box-shadow: inset 0 0 0 1px var(--divider-color); color: var(--secondary-text-color); }
.row.checked .ico { filter: grayscale(1); opacity: .45; }
.row.checked .name, .row.checked .spec { text-decoration: line-through; text-decoration-thickness: 2px; }
.row.checked .circle { background: var(--secondary-text-color); border-color: var(--secondary-text-color); color: #fff; opacity: .6; }
.row.checking .circle { background: var(--acc); border-color: var(--acc); color: #fff; }
.row.checking { opacity: .6; transition: opacity .25s; }
.empty.small { padding: 4px 8px 14px; }
.empty.small svg { width: 44px; height: 44px; }
`;

class EinkaufslisteCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._items = [];
    this._loaded = false;
    this._pending = new Map(); // uid -> {status, ts}
    this._assignOverride = new Map(); // key -> {store, ts}
    this._localChecked = new Map(); // uid -> ts (abgehakt, bevor HA es bestätigt)
    this._recentOpen = false;
    this._tab = "";
    this._unsub = null;
    this._seen = new Set();
    this._sig = "";
  }

  static getStubConfig(hass) {
    const ent = Object.keys(hass.states).find(
      (e) => e.startsWith("todo.") && hass.states[e].attributes.einkaufsliste
    );
    return { entity: ent || "", layout: "grid", accent: "bring", show_recent: true, show_tabs: true };
  }

  static getConfigForm() {
    return {
      schema: [
        { name: "entity", required: true, selector: { entity: { domain: "todo", integration: "einkaufsliste" } } },
        { name: "title", selector: { text: {} } },
        {
          type: "grid",
          name: "",
          schema: [
            {
              name: "layout",
              selector: { select: { mode: "dropdown", options: [
                { value: "grid", label: "Kacheln" }, { value: "list", label: "Liste" } ] } },
            },
            {
              name: "accent",
              selector: { select: { mode: "dropdown", options: [
                { value: "bring", label: "Bring-Rot" }, { value: "smaragd", label: "Smaragd" },
                { value: "ozean", label: "Ozean" }, { value: "violett", label: "Violett" },
                { value: "orange", label: "Orange" }, { value: "graphit", label: "Graphit" },
                { value: "theme", label: "Theme-Farbe" } ] } },
            },
            {
              name: "sort",
              selector: { select: { mode: "dropdown", options: [
                { value: "bring", label: "Wie in Bring" }, { value: "alpha", label: "Alphabetisch" } ] } },
            },
            { name: "recent_limit", selector: { number: { min: 0, max: 60, mode: "box" } } },
          ],
        },
        { name: "show_tabs", selector: { boolean: {} } },
        { name: "show_recent", selector: { boolean: {} } },
        { name: "show_icons", selector: { boolean: {} } },
      ],
      computeLabel: (s) =>
        ({
          entity: "Einkaufsliste",
          title: "Titel (optional)",
          layout: "Darstellung",
          accent: "Farbe",
          sort: "Sortierung",
          recent_limit: "Anzahl „Zuletzt gekauft“",
          show_tabs: "Reiter für Geschäfte anzeigen",
          show_recent: "„Zuletzt gekauft“ anzeigen",
          show_icons: "Bring-Bilder statt Emojis verwenden",
        })[s.name],
    };
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error("Bitte eine Einkaufsliste (todo-Entität) auswählen.");
    const old = this._config;
    this._config = {
      layout: "grid", accent: "bring", sort: "bring", show_recent: true, show_icons: false, show_tabs: true,
      recent_limit: 24, ...config,
    };
    if (old && old.entity !== this._config.entity) this._unsubscribe();
    this._build();
    this._subscribe();
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._subscribe();
    this._renderHeader();
    this._renderItems();
  }

  connectedCallback() {
    this._subscribe();
    clearInterval(this._dayTimer);
    this._dayTimer = setInterval(() => { this._sig = ""; this._renderItems(); }, 60000);
  }
  disconnectedCallback() { this._unsubscribe(); clearInterval(this._dayTimer); }

  getCardSize() { return 3 + Math.ceil(this._open().length / 4); }
  getGridOptions() { return { columns: 12, min_columns: 4, rows: "auto" }; }

  // ------------------------------------------------------------------ data
  async _subscribe() {
    if (!this._hass || !this._config || this._unsub || this._subscribing || !this.isConnected) return;
    this._subscribing = true;
    try {
      this._unsub = await this._hass.connection.subscribeMessage(
        (msg) => {
          this._items = msg.items || [];
          this._loaded = true;
          this._error = null;
          const now = Date.now();
          for (const [uid, p] of this._pending) {
            const it = this._items.find((i) => i.uid === uid);
            if (!it || it.status === p.status || now - p.ts > 8000) this._pending.delete(uid);
          }
          this._renderItems();
        },
        { type: "todo/item/subscribe", entity_id: this._config.entity }
      );
    } catch (e) {
      this._error = e && e.message ? e.message : "Liste konnte nicht geladen werden.";
      this._renderItems();
    }
    this._subscribing = false;
  }

  _unsubscribe() {
    if (this._unsub) {
      try { this._unsub(); } catch (_) {}
      this._unsub = null;
    }
  }

  get _attrs() {
    return this._hass?.states?.[this._config.entity]?.attributes || {};
  }

  get _stores() {
    return Array.isArray(this._attrs.stores) ? this._attrs.stores : [];
  }

  _storeById(id) {
    return id ? this._stores.find((s) => s.id === id) || null : null;
  }

  _storeIdOf(item) {
    const key = item.summary.trim().toLowerCase();
    const now = Date.now();
    const o = this._assignOverride.get(key);
    const server = (this._attrs.assignments || {})[key] || null;
    if (o) {
      if ((o.store || null) === server || now - o.ts > 10000) this._assignOverride.delete(key);
      else return this._storeById(o.store) ? o.store : null;
    }
    return this._storeById(server) ? server : null;
  }

  _status(item) {
    const p = this._pending.get(item.uid);
    return p ? p.status : item.status;
  }

  _sorted(list) {
    if (this._config.sort === "alpha") return [...list].sort((a, b) => a.summary.localeCompare(b.summary, "de"));
    return list;
  }

  _open() { return this._sorted(this._items.filter((i) => this._status(i) === "needs_action")); }

  /** Heute abgehakte Artikel: bleiben durchgestrichen am Ende der Liste bis 0 Uhr. */
  _checkedTs(item) {
    if (this._status(item) !== "completed") return null;
    const server = this._attrs.checked || {};
    let ts = null;
    if (Object.prototype.hasOwnProperty.call(server, item.uid)) {
      ts = Number(server[item.uid]) * 1000;
      this._localChecked.delete(item.uid);
    } else if (this._localChecked.has(item.uid)) {
      ts = this._localChecked.get(item.uid);
      if (Date.now() - ts > 60000) { this._localChecked.delete(item.uid); ts = null; }
    }
    if (ts === null) return null;
    const midnight = new Date(); midnight.setHours(0, 0, 0, 0);
    return ts >= midnight.getTime() ? ts : null;
  }

  _checked() {
    return this._items
      .map((i) => [i, this._checkedTs(i)])
      .filter(([, ts]) => ts !== null)
      .sort((a, b) => a[1] - b[1])
      .map(([i]) => i);
  }

  _recent() { return this._items.filter((i) => this._status(i) === "completed" && this._checkedTs(i) === null); }

  async _call(service, data, domain = "todo") {
    try {
      await this._hass.callService(domain, service, { entity_id: this._config.entity, ...data });
    } catch (e) {
      this._error = e && e.message ? e.message : "Aktion fehlgeschlagen.";
      this._pending.clear();
      this._assignOverride.clear();
      this._renderItems();
    }
  }

  _assign(name, storeId) {
    const key = name.trim().toLowerCase();
    this._assignOverride.set(key, { store: storeId || null, ts: Date.now() });
    this._call("set_store", { item: name, store: storeId || "" }, "einkaufsliste");
  }

  _setStatus(uid, status) {
    this._pending.set(uid, { status, ts: Date.now() });
    this._call("update_item", { item: uid, status });
  }

  /** Wieder auf die Liste setzen – im Geschäfts-Reiter direkt diesem Geschäft zuordnen. */
  _readd(uid) {
    const item = this._items.find((i) => i.uid === uid);
    if (item && this._tab) this._assign(item.summary, this._tab);
    this._setStatus(uid, "needs_action");
  }

  _add(text) {
    let name = text.trim();
    if (!name) return;
    let spec = "";
    const idx = name.indexOf(",");
    if (idx > 0) { spec = name.slice(idx + 1).trim(); name = name.slice(0, idx).trim(); }
    if (this._tab) this._assign(name, this._tab);
    const existing = this._items.find((i) => i.summary.toLowerCase() === name.toLowerCase());
    if (existing) {
      this._pending.set(existing.uid, { status: "needs_action", ts: Date.now() });
      const data = { item: existing.uid, status: "needs_action" };
      if (spec) data.description = spec;
      this._call("update_item", data);
      this._renderItems();
      return;
    }
    const data = { item: name };
    if (spec) data.description = spec;
    this._call("add_item", data);
  }

  // ------------------------------------------------------------------ render
  _build() {
    const [a1, a2] = ACCENTS[this._config.accent] || ACCENTS.bring;
    this.shadowRoot.innerHTML = `
      <style>${STYLE}</style>
      <ha-card lang="de" style="--acc:${a1};--acc2:${a2}">
        <div class="wrap">
          <header>
            <div class="badge">${ICONS.cart}</div>
            <div class="titles"><div class="title"></div><div class="sub"></div></div>
            <button class="icon-btn" id="refresh" title="Aktualisieren">${ICONS.refresh}</button>
          </header>
          <form class="add" autocomplete="off">
            <input id="input" enterkeyhint="done" placeholder="Was brauchst du? (z. B. Milch, 2 Liter)">
            <button class="add-btn" type="submit" title="Hinzufügen">${ICONS.plus}</button>
          </form>
          <div class="suggest"></div>
          <div class="tabs" hidden></div>
          <div class="items"></div>
          <div class="recent-wrap ${this._recentOpen ? "open" : ""}" hidden>
            <button class="recent-toggle" type="button">Zuletzt gekauft <span class="cnt"></span>${ICONS.chevron}</button>
            <div class="recent grid"></div>
          </div>
          <div class="err-slot"></div>
        </div>
        <div class="sheet" hidden>
          <div class="panel">
            <h3>Artikel bearbeiten</h3>
            <label>Name</label><input id="ed-name">
            <label>Beschreibung (Menge, Marke …)</label><input id="ed-spec" placeholder="z. B. 2 Liter, Bio">
            <label>Geschäft</label><div class="store-pick"></div>
            <div class="actions">
              <button class="btn-del" type="button">Löschen</button>
              <button class="btn-cancel" type="button">Abbrechen</button>
              <button class="btn-save" type="button">Speichern</button>
            </div>
          </div>
        </div>
      </ha-card>`;
    const $ = (s) => this.shadowRoot.querySelector(s);
    this._els = {
      title: $(".title"), sub: $(".sub"), items: $(".items"), recentWrap: $(".recent-wrap"), recent: $(".recent"),
      cnt: $(".cnt"), input: $("#input"), suggest: $(".suggest"), err: $(".err-slot"), sheet: $(".sheet"),
      edName: $("#ed-name"), edSpec: $("#ed-spec"), refresh: $("#refresh"), tabs: $(".tabs"), pick: $(".store-pick"),
    };

    $("form.add").addEventListener("submit", (ev) => {
      ev.preventDefault();
      this._add(this._els.input.value);
      this._els.input.value = "";
      this._renderSuggest();
    });
    this._els.input.addEventListener("input", () => this._renderSuggest());
    this._els.suggest.addEventListener("click", (ev) => {
      const chip = ev.target.closest(".chip");
      if (!chip) return;
      this._readd(chip.dataset.uid);
      this._els.input.value = "";
      this._renderSuggest();
      this._renderItems();
    });
    this._els.refresh.addEventListener("click", async () => {
      this._els.refresh.classList.add("spin");
      try {
        await this._hass.callService("homeassistant", "update_entity", { entity_id: this._config.entity });
      } catch (_) {}
      setTimeout(() => this._els.refresh.classList.remove("spin"), 600);
    });
    $(".recent-toggle").addEventListener("click", () => {
      this._recentOpen = !this._recentOpen;
      this._els.recentWrap.classList.toggle("open", this._recentOpen);
    });
    this._els.tabs.addEventListener("click", (ev) => {
      const tab = ev.target.closest(".tab");
      if (!tab) return;
      this._tab = tab.dataset.tab || "";
      this._renderItems();
    });

    // Antippen = erledigt / wieder hinzufügen, langes Drücken = bearbeiten
    const onTap = (ev) => {
      const el = ev.target.closest("[data-uid]");
      if (!el) return;
      if (this._longPressed) { this._longPressed = false; return; }
      const uid = el.dataset.uid;
      if (el.closest(".recent")) {
        el.classList.add("readd");
        setTimeout(() => { this._readd(uid); this._renderItems(); }, 300);
      } else if (el.classList.contains("checked")) {
        // Rückgängig: wieder auf die Liste
        this._localChecked.delete(uid);
        el.classList.add("unchecking");
        setTimeout(() => { this._setStatus(uid, "needs_action"); this._renderItems(); }, 180);
      } else {
        this._localChecked.set(uid, Date.now());
        el.classList.add("checking");
        setTimeout(() => { this._setStatus(uid, "completed"); this._renderItems(); }, 260);
      }
    };
    const startPress = (ev) => {
      const el = ev.target.closest("[data-uid]");
      if (!el) return;
      clearTimeout(this._pressTimer);
      this._pressTimer = setTimeout(() => { this._markLongPress(); this._openEditor(el.dataset.uid); }, 550);
    };
    const endPress = () => clearTimeout(this._pressTimer);
    const logoFailed = (img) => {
      const tab = img.closest(".icon-tab[data-domain]");
      if (tab) {
        failedLogos.add(tab.dataset.domain);
        const n = tab.querySelector(".n")?.textContent || "";
        const emoji = tab.dataset.emoji;
        tab.classList.replace("icon-tab", "name-tab");
        tab.style.setProperty("--h", hueFor(tab.dataset.name));
        tab.innerHTML = (emoji && emoji !== "🛒" && emoji !== "🏪" ? `<span class="nt-emoji">${esc(emoji)}</span>` : "") +
          `<span class="nt-name">${esc(tab.dataset.name)}</span><span class="n">${esc(n)}</span>`;
        return true;
      }
      return false;
    };
    // Google liefert für unbekannte Seiten einen winzigen Platzhalter (Weltkugel) – dann lieber den Namen zeigen
    this._els.tabs.addEventListener("load", (ev) => {
      const img = ev.target;
      if (img.tagName === "IMG" && img.naturalWidth > 0 && img.naturalWidth < 32) logoFailed(img);
    }, true);
    const onImgError = (ev) => {
      const img = ev.target;
      if (img.tagName !== "IMG") return;
      if (logoFailed(img)) return;
      if (img.dataset.cls) {
        img.outerHTML = `<span class="${img.dataset.cls} sletter" style="--h:${img.dataset.hue}">${esc(img.dataset.letter)}</span>`;
        return;
      }
      failedImages.add(img.dataset.slug);
      const name = img.closest("[data-name]")?.dataset.name || "";
      img.outerHTML = fallbackIcon(name);
    };
    for (const container of [this._els.items, this._els.recent]) {
      container.addEventListener("click", onTap);
      container.addEventListener("pointerdown", startPress);
      container.addEventListener("pointerup", endPress);
      container.addEventListener("pointerleave", endPress);
      container.addEventListener("pointercancel", endPress);
      container.addEventListener("contextmenu", (ev) => {
        const el = ev.target.closest("[data-uid]");
        if (!el) return;
        ev.preventDefault();
        clearTimeout(this._pressTimer);
        this._markLongPress();
        if (this._els.sheet.hidden) this._openEditor(el.dataset.uid);
      });
    }
    for (const container of [this._els.items, this._els.recent, this._els.tabs, this._els.pick]) {
      container.addEventListener("error", onImgError, true);
    }

    // Editor
    const sheet = this._els.sheet;
    sheet.addEventListener("click", (ev) => { if (ev.target === sheet) this._closeEditor(); });
    $(".btn-cancel").addEventListener("click", () => this._closeEditor());
    $(".btn-del").addEventListener("click", () => {
      const uid = this._editUid;
      this._items = this._items.filter((i) => i.uid !== uid);
      this._call("remove_item", { item: [uid] });
      this._closeEditor();
      this._renderItems();
    });
    $(".btn-save").addEventListener("click", () => this._saveEditor());
    this._els.pick.addEventListener("click", (ev) => {
      const b = ev.target.closest("button[data-store]");
      if (!b) return;
      this._editStore = b.dataset.store || "";
      for (const x of this._els.pick.querySelectorAll("button")) x.classList.toggle("sel", x === b);
    });
    for (const inp of [this._els.edName, this._els.edSpec]) {
      inp.addEventListener("keydown", (ev) => { if (ev.key === "Enter") this._saveEditor(); if (ev.key === "Escape") this._closeEditor(); });
    }

    this._sig = "";
    this._seen = new Set();
    this._renderHeader();
    this._renderItems();
  }

  _markLongPress() {
    this._longPressed = true;
    clearTimeout(this._lpReset);
    this._lpReset = setTimeout(() => { this._longPressed = false; }, 900);
  }

  _openEditor(uid) {
    const item = this._items.find((i) => i.uid === uid);
    if (!item) return;
    this._editUid = uid;
    this._editStore = this._storeIdOf(item) || "";
    this._editStoreOrig = this._editStore;
    this._els.edName.value = item.summary;
    this._els.edSpec.value = item.description || "";
    const stores = this._stores;
    this._els.pick.innerHTML = stores.length
      ? [`<button type="button" data-store="" class="${this._editStore ? "" : "sel"}"><span class="slogo semoji">🛒</span>Überall</button>`,
         ...stores.map((s) => `<button type="button" data-store="${esc(s.id)}" class="${this._editStore === s.id ? "sel" : ""}">
            ${storeLogo(s)}${esc(s.name)}</button>`)].join("")
      : `<div class="store-empty">Wähle deine Geschäfte unter <b>Einstellungen → Geräte &amp; Dienste → Einkaufsliste → Konfigurieren</b>.</div>`;
    this._els.sheet.hidden = false;
  }

  _closeEditor() {
    this._els.sheet.hidden = true;
    this._editUid = null;
  }

  _saveEditor() {
    const item = this._items.find((i) => i.uid === this._editUid);
    if (!item) return this._closeEditor();
    const name = this._els.edName.value.trim();
    const spec = this._els.edSpec.value.trim();
    if (!name) return;
    const data = { item: item.uid, description: spec };
    const renamed = name !== item.summary;
    if (renamed) data.rename = name;
    const storeChanged = this._editStore !== this._editStoreOrig;
    item.summary = name;
    item.description = spec;
    this._call("update_item", data);
    if (storeChanged) this._assign(name, this._editStore);
    this._closeEditor();
    this._renderItems();
  }

  _renderHeader() {
    if (!this._els || !this._hass) return;
    const name = this._config.title || this._attrs.list_name || this._attrs.friendly_name || "Einkaufsliste";
    if (this._els.title.textContent !== name) this._els.title.textContent = name;
  }

  _renderSub() {
    if (!this._els) return;
    const n = this._open().length;
    const d = this._checked().length;
    const done = d ? ` · ${d} erledigt` : "";
    this._els.sub.innerHTML = !this._loaded
      ? "Wird geladen …"
      : n === 0 ? `Alles erledigt${d ? " 🎉" : ""}` : `<b>${n}</b> Artikel auf der Liste${done}`;
  }

  _isNew(item, scope) {
    const key = scope + ":" + item.uid;
    if (this._seen.has(key)) return "";
    this._seen.add(key);
    return this._firstPaint ? "" : " new";
  }

  _tile(item, scope, badgeStore = null, checked = false) {
    const icons = this._config.show_icons === true;
    const spec = item.description ? `<span class="spec">${esc(item.description)}</span>` : "";
    const badge = badgeStore ? `<span class="badge-store">${storeLogo(badgeStore)}</span>` : "";
    if (this._config.layout === "list" && scope !== "r") {
      return `<button class="row${checked ? " checked" : ""}${this._isNew(item, scope + (checked ? "x" : ""))}" data-uid="${esc(item.uid)}" data-name="${esc(item.summary)}">
        <span class="ico">${iconHtml(item.summary, icons)}</span>
        <span class="txt"><span class="name">${esc(item.summary)}</span>${spec}</span>
        ${badge}<span class="circle">${ICONS.check}</span></button>`;
    }
    return `<button class="tile${checked ? " checked" : ""}${this._isNew(item, scope + (checked ? "x" : ""))}" data-uid="${esc(item.uid)}" data-name="${esc(item.summary)}" title="${esc(item.summary)}">
      ${badge}<span class="ico">${iconHtml(item.summary, icons)}</span>
      <span class="name">${esc(item.summary)}</span>${spec}
      <span class="tick">${ICONS.check}</span></button>`;
  }

  _block(items, scope, badgeStore = null, checked = []) {
    const cls = this._config.layout === "list" ? "list" : "grid";
    return `<div class="${cls}">${items.map((i) => this._tile(i, scope, badgeStore)).join("")}${
      checked.map((i) => this._tile(i, scope, badgeStore, true)).join("")}</div>`;
  }

  _renderItems() {
    if (!this._els || !this._config) return;
    this._renderSub();
    const open = this._open();
    const els = this._els;
    const useTabs = this._config.show_tabs !== false;

    // Artikel nach Geschäft gruppieren
    const general = [];
    const byStore = new Map();
    for (const item of open) {
      const sid = useTabs ? this._storeIdOf(item) : null;
      if (!sid) general.push(item);
      else {
        if (!byStore.has(sid)) byStore.set(sid, []);
        byStore.get(sid).push(item);
      }
    }
    const checked = this._checked();
    const generalDone = [];
    const byStoreDone = new Map();
    for (const item of checked) {
      const sid = useTabs ? this._storeIdOf(item) : null;
      if (!sid) generalDone.push(item);
      else {
        if (!byStoreDone.has(sid)) byStoreDone.set(sid, []);
        byStoreDone.get(sid).push(item);
      }
    }
    const storeTabs = this._stores.filter((s) => byStore.has(s.id) || byStoreDone.has(s.id));
    if (this._tab && !storeTabs.some((s) => s.id === this._tab)) this._tab = "";

    const sig = JSON.stringify([
      this._loaded, this._error, this._tab, this._config.layout,
      open.map((i) => [i.uid, i.summary, i.description, useTabs ? this._storeIdOf(i) : null]),
      checked.map((i) => [i.uid, i.summary, i.description, useTabs ? this._storeIdOf(i) : null]),
      this._recent().map((i) => [i.uid, i.summary]),
      storeTabs.map((s) => s.id),
    ]);
    if (sig === this._sig) return;
    this._sig = sig;
    this._firstPaint = this._seen.size === 0;

    // Reiter
    els.tabs.hidden = storeTabs.length === 0;
    if (storeTabs.length) {
      const tabCls = (id) => (this._tab === id ? "active" : "");
      const nameTab = (st, n) => {
        const emoji = st.emoji && st.emoji !== "🏪" && st.emoji !== "🛒" ? `<span class="nt-emoji">${esc(st.emoji)}</span>` : "";
        return `<button class="tab name-tab ${tabCls(st.id)}" data-tab="${esc(st.id)}" style="--h:${hueFor(st.name)}"
          title="${esc(st.name)}">${emoji}<span class="nt-name">${esc(st.name)}</span><span class="n">${n}</span></button>`;
      };
      els.tabs.innerHTML = [
        `<button class="tab icon-tab cart-tab ${tabCls("")}" data-tab="" title="Allgemein" aria-label="Allgemein">
          <span class="cart-ico">${ICONS.cart}</span><span class="n">${general.length}</span></button>`,
        ...storeTabs.map((st) => {
          const n = (byStore.get(st.id) || []).length;
          if (!st.domain || failedLogos.has(st.domain)) return nameTab(st, n);
          return `<button class="tab icon-tab ${tabCls(st.id)}" data-tab="${esc(st.id)}" data-domain="${esc(st.domain)}"
            data-name="${esc(st.name)}" data-emoji="${esc(st.emoji || "")}" title="${esc(st.name)}" aria-label="${esc(st.name)}">
            ${storeLogo(st)}<span class="n">${n}</span></button>`;
        }),
      ].join("");
    }

    // Inhalt
    if (!this._loaded && !this._error) {
      els.items.innerHTML = `<div class="empty">Liste wird geladen …</div>`;
    } else if (open.length === 0 && checked.length === 0) {
      els.items.innerHTML = `<div class="empty">${ICONS.party}<div class="big">Alles eingekauft!</div>
        <div>Füge oben etwas hinzu oder tippe unten auf einen Artikel.</div></div>`;
    } else if (this._tab) {
      const store = this._storeById(this._tab);
      const own = byStore.get(this._tab) || [];
      const ownDone = byStoreDone.get(this._tab) || [];
      let html = `<div class="section">${storeLogo(store)}Nur bei ${esc(store.name)}</div>${this._block(own, "s", store, ownDone)}`;
      if (general.length || generalDone.length) {
        html += `<div class="section"><span class="slogo semoji">🛒</span>Überall erhältlich</div>${this._block(general, "g", null, generalDone)}`;
      }
      els.items.innerHTML = html;
    } else {
      const others = open.length - general.length;
      let html = general.length || generalDone.length
        ? (general.length ? "" : `<div class="empty small">${ICONS.party}<div class="big">Alles erledigt!</div></div>`) +
          this._block(general, "g", null, generalDone)
        : `<div class="empty"><div class="big">Nichts Allgemeines</div><div>Alle Artikel gehören zu einem Geschäft.</div></div>`;
      if (others) html += `<div class="hint">+ ${others} Artikel in den Geschäfts-Reitern</div>`;
      els.items.innerHTML = html;
    }

    const recent = this._recent().slice(0, Number(this._config.recent_limit ?? 24));
    const showRecent = this._config.show_recent !== false && recent.length > 0;
    els.recentWrap.hidden = !showRecent;
    if (showRecent) {
      els.cnt.textContent = recent.length;
      els.recent.innerHTML = recent.map((i) => this._tile(i, "r")).join("");
    }

    els.err.innerHTML = this._error ? `<div class="error">${esc(this._error)}</div>` : "";
    this._renderSuggest();
  }

  _renderSuggest() {
    if (!this._els) return;
    const q = this._els.input.value.split(",")[0].trim().toLowerCase();
    if (!q) { this._els.suggest.innerHTML = ""; return; }
    const hits = this._recent().filter((i) => i.summary.toLowerCase().includes(q)).slice(0, 6);
    this._els.suggest.innerHTML = hits
      .map((i) => `<button class="chip" type="button" data-uid="${esc(i.uid)}">+ ${esc(i.summary)}</button>`)
      .join("");
  }
}

if (!customElements.get("einkaufsliste-card")) {
  customElements.define("einkaufsliste-card", EinkaufslisteCard);
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "einkaufsliste-card",
    name: "Einkaufsliste (Bring!)",
    description: "Deine Bring!-Einkaufsliste als hübsche Kacheln – mit Reitern für deine Geschäfte.",
    preview: true,
    documentationURL: "https://github.com/domiundergroun/Einkaufsliste",
  });
  console.info(`%c EINKAUFSLISTE-CARD %c v${CARD_VERSION} `,
    "background:#ee524f;color:#fff;font-weight:700;border-radius:4px 0 0 4px;padding:2px 4px",
    "background:#333;color:#fff;border-radius:0 4px 4px 0;padding:2px 4px");
}

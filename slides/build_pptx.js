// Builds slides/pitch.pptx (10 x 5.625 in, the Google Slides default) from the figures in ../figures.
// Same content as presentation.tex, with the speaker notes from ../docs/speaker_notes.md.
// Import into Google Slides with File > Import slides.
// Run from slides/:  npm install pptxgenjs@3.12.0  then  node build_pptx.js
const path = require("path");
const pptxgen = require("pptxgenjs");

const FIG = (f) => path.join(__dirname, "..", "figures", f);
const INK = "0B0B0B", INK2 = "52514E", MUTED = "898781", RULE = "E1E0D9", DARK = "1A1A19", LIGHT = "F0EFEC";
const GOOD = "0A8A0A", WARN = "A06E00", BAD = "C03030";
const FONT = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "Two independent eyes on every direction";
pres.subject = "Sensor modality comparison: compare and design (Exercise 4)";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };

pres.defineSlideMaster({
  title: "DARK",
  background: { color: DARK },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: "FCFCFB" },   // the figures' surface color, so they sit flush
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.45, y: 0.22, w: 9.1, h: 0.6, fontFace: FONT,
      fontSize: 24, bold: true, color: INK, valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 9.3, y: 5.25, w: 0.4, h: 0.25, fontFace: FONT, fontSize: 9, color: MUTED, align: "right" },
});

const notes = {
  title: "Our question was: what does a normal private car need to see to drive itself in the city and on the highway, and is Level 5 possible today? One physics model, fed by official datasheets, answers both.",
  req: "We started from what the car must see, not from the sensors. Each number is one driving scenario and one formula. To stop for a car from 130 km/h with one second to react and comfortable braking, the car must see 253 m ahead. For a pedestrian on a 70 km/h city road, 82 m. At the sides, cross traffic at 60 km/h needs 81 m so we can pull out. Behind, a lane change with a faster car coming needs 96 m. Around the car, 15 m for pedestrians and the near field down to 10 cm. Our design rule: on every bearing, at least two independent modalities must reach that range, so one can fail or be fooled.",
  spider: "Here are the four modalities on the professor's six axes, under four conditions. The scores are not hand-set: each one comes from datasheet numbers and one physics law per effect, for example Koschmieder for fog or the radar equation with rain attenuation. The camera wins on detail and color in daylight, but at night its contrast falls to 0.16, because only the low beam lights a pedestrian. In fog the optical sensors lose about half their range; radar keeps 0.75 and owns speed measurement with 0.07 m/s Doppler. Lidar gives the best 3D, day and night. Thermal sees living objects in the dark. The gray area is the whole suite: the best modality on each axis. No single modality covers it, so we need all four.",
  design: "So the suite has 20 sensors. Each is a real product with its maker's datasheet, and each is there because a number asks for it. An Innoviz InnovizTwo lidar in the bumper sees a dark car at 300 m: it covers the 253 m requirement day and night. A Hesai OT128 on the roof covers the sides and the rear. Five smartmicro DRVEGRD 171 4D radars, front and corners, measure speed and still reach 239 m in fog. Seven Supertek cameras with OmniVision's 8-megapixel OX08B40 give color, signs and lights; the 30-degree tele sees a car at 464 m. Four SENSING fisheyes with Sony's ISX031 cover the near field. One Raytron Horus640 thermal camera is there because at night the camera only reaches 63 m but we need 82. A u-blox ZED-F9K with RTK and an HD map gives lane-level position. Total: about 11,000 USD for the sensors.",
  coverage: "This is the core result. For every direction and condition we count how many modalities still reach the required range. Green is two or more, amber one, red none. Outer ring cars, middle ring pedestrians, inner ring the near field. In clear weather and at night it's green all round. In dense fog, nothing reaches 253 m ahead: the radar gets 239 m, the lidar 114 m, and straight behind only the rear camera reaches 96 m. In snow only the camera does. And the near field is amber everywhere: below about 30 cm and beside the doors only the cameras see, because lidar and radar have a minimum range. That's our first thing to fix.",
  l5: "Level 5 means no limit at all on roads or weather. So we asked: how fast may our car drive so that two modalities still cover its stopping distance? In clear weather, 142 km/h. At night with pedestrians around, 78. In fog with 200 m visibility, 84 for cars and 77 with pedestrians. Below 50 m visibility, roughly 35 to 65, close to the 50 km/h a German driver is allowed. So the car can drive, but it has to slow down like a careful human. On top of that, no datasheet covers a sensor blocked by snow or ice, rare events need billions of test kilometres, and the law approves only defined operating domains.",
  summary: "To sum up: 20 sensors, 11,000 dollars, two modalities on every bearing in clear weather and at night, and 84 km/h in dense fog. Our answer: Level 4 in city and highway inside a speed envelope, yes. True Level 5, anywhere and in any weather, is not possible today. The next gaps to close are an ultrasonic ring for the near field, a rear radar for straight behind, and longer-range imaging radar for fog. Thank you.",
};

const body = (extra) => Object.assign({ fontFace: FONT, color: INK, isTextBox: true, margin: 0, valign: "top" }, extra);
// keep a number and its unit on one line
const nb = (t) => t.replace(/(\d) (m\b|m\/s|km\/h|dB|USD|MP|s\b)/g, "$1\u00A0$2");
const cell = (text, o = {}) => ({ text: nb(text), options: Object.assign({ fontFace: FONT, fontSize: 12, color: INK, valign: "middle",
  margin: [2, 4, 2, 4] }, o) });
const head = (text, o = {}) => cell(text, Object.assign({ bold: true, color: INK2, border: [{ type: "none" }, { type: "none" },
  { pt: 1, color: INK2 }, { type: "none" }] }, o));
const rowBorder = [{ type: "none" }, { type: "none" }, { pt: 0.75, color: RULE }, { type: "none" }];
const table = (rows) => rows.map((r) => r.map((c) => (c.options && c.options.border ? c
  : { text: c.text, options: Object.assign({ border: rowBorder }, c.options) })));

// ---- title
let s = pres.addSlide({ masterName: "DARK" });
s.addText("Two independent eyes on every direction", body({ x: 0.6, y: 1.55, w: 8.8, h: 0.9, fontSize: 36, bold: true,
  color: "FFFFFF", valign: "middle" }));
s.addText("Sensor modality comparison: compare and design a city + highway car", body({ x: 0.6, y: 2.5, w: 8.8, h: 0.5,
  fontSize: 18, color: LIGHT }));
s.addText("Team: names TBD  ·  3DSSF – Kozma – Exercise 4", body({ x: 0.6, y: 3.6, w: 8.8, h: 0.4, fontSize: 14,
  color: "C3C2B7" }));
s.addText("One physics model, fed by official datasheets, drives every chart and number in this talk.",
  body({ x: 0.6, y: 4.7, w: 8.8, h: 0.35, fontSize: 12, italic: true, color: "C3C2B7" }));
s.addNotes(notes.title);

// ---- 1. requirements
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("What must the car see, and how far?", { placeholder: "title" });
s.addImage({ path: FIG("requirements.png"), x: 0.35, y: 0.95, w: 4.35, h: 4.35, altText:
  "Required detection range per direction: car 253 m ahead, 81 m at the sides, 96 m behind; pedestrian 82 m ahead and 15 m around; near field 0.1 to 5 m." });
s.addTable(table([
  [head("where"), head("scenario"), head("range", { align: "right" })],
  [cell("ahead"), cell("stop for a car from 130 km/h"), cell("253 m", { bold: true, align: "right" })],
  [cell("ahead"), cell("stop for a pedestrian from 70 km/h"), cell("82 m", { bold: true, align: "right" })],
  [cell("sides"), cell("pull out before cross traffic at 60 km/h"), cell("81 m", { bold: true, align: "right" })],
  [cell("behind"), cell("lane change, car closing at 60 km/h"), cell("96 m", { bold: true, align: "right" })],
  [cell("around"), cell("jogger during a 4.9 s turn"), cell("15 m", { bold: true, align: "right" })],
  [cell("around"), cell("kerbs, a child next to the car"), cell("0.1–5 m", { bold: true, align: "right" })],
]), { x: 4.95, y: 1.0, w: 4.65, colW: [0.75, 3.05, 0.85], rowH: 0.36 });
s.addText("Stopping distance v·1 s + v²/(2·3 m/s²): plan to stop without emergency braking.",
  body({ x: 4.95, y: 3.65, w: 4.65, h: 0.35, fontSize: 10, color: MUTED }));
s.addText([
  { text: "Design rule: ", options: { bold: true } },
  { text: "on every bearing, at least " },
  { text: "two independent modalities", options: { bold: true } },
  { text: " (camera, lidar, radar, thermal) reach the required range, so one can fail or be fooled." },
], body({ x: 4.95, y: 4.15, w: 4.65, h: 0.9, fontSize: 14 }));
s.addNotes(notes.req);

// ---- 2. compare
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Compare: no modality wins every axis in every condition", { placeholder: "title" });
s.addImage({ path: FIG("spider_conditions.png"), x: 0.3, y: 0.85, w: 9.4, h: 9.4 * 3.75 / 10, altText:
  "Four spider charts (clear day, night, fog or heavy rain, snow or glare or tunnel) comparing camera, lidar, radar and thermal on contrast, range, color, speed, 3D and living objects." });
const caps = [
  ["Camera", "detail and color; contrast 0.16 at night, range 0.42 in fog"],
  ["Radar", "speed (0.07 m/s Doppler), keeps its range in fog; no detail"],
  ["Lidar", "best 3D, same day and night; about half the range in fog"],
  ["Thermal", "living objects, day or night; short range"],
];
caps.forEach(([k, v], i) => s.addText([{ text: k + ": ", options: { bold: true } }, { text: v }],
  body({ x: 0.45 + i * 2.3, y: 4.5, w: 2.15, h: 0.75, fontSize: 12 })));
s.addNotes(notes.spider);

// ---- 3. design
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Design: 20 sensors, each one asked for by a number", { placeholder: "title" });
s.addImage({ path: FIG("suite_layout.png"), x: 0.15, y: 0.95, w: 4.0, h: 4.0, altText:
  "Mounting positions on the car: lidar, radar, thermal and fisheye in the front bumper, two cameras at the windscreen, 360-degree lidar on the roof, radars at the four corners, cameras on the mirrors, camera and fisheye at the rear." });
const D = (n, sensor, why, usd) => [cell(n, { align: "right" }), cell(sensor), cell(why), cell(usd, { align: "right" })];
s.addTable(table([
  [head("#", { align: "right" }), head("sensor"), head("why: the number from our model"), head("USD", { align: "right" })],
  D("1", "Innoviz InnovizTwo lidar, bumper", "dark car at 300 m, dark pedestrian at 231 m, day or night", "1,000"),
  D("1", "Hesai OT128 lidar, roof", "360° 3D: cars at 214 m, sides need 81 m", "3,000"),
  D("5", "smartmicro DRVEGRD 171 radar", "Doppler 0.07 m/s; 239 m in fog; corners = 2nd modality sideways", "2,000"),
  D("3", "Supertek OX08B40 8 MP camera, 30°/60°, rear 60°", "color, signs, lights; tele: car at 464 m; 140 dB HDR", "900"),
  D("4", "Supertek OX08B40 camera 120°, mirrors", "cross traffic: 113 m > 81 m needed", "1,200"),
  D("4", "SENSING ISX031 3 MP fisheye", "near field 0.1–5 m all round", "1,836"),
  D("1", "Raytron Horus640-D thermal", "night pedestrians: camera reaches 63 m, 82 m needed", "800"),
  D("1", "u-blox ZED-F9K + HD map", "lane-level position (< 0.2 m RTK)", "250"),
  [cell("20", { bold: true, align: "right" }), cell(""), cell("sensors only; prices mostly estimates", { bold: true }),
    cell("10,986", { bold: true, align: "right" })],
]).map((r) => r.map((c) => ({ text: c.text, options: Object.assign({}, c.options, { fontSize: 11 }) }))),
{ x: 4.2, y: 0.95, w: 5.55, colW: [0.3, 2.1, 2.55, 0.6] });
s.addNotes(notes.design);

// ---- 4. coverage
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Coverage: how many modalities reach the required range?", { placeholder: "title" });
s.addImage({ path: FIG("coverage_conditions.png"), x: 0.45, y: 0.8, w: 9.1, h: 9.1 * 3.9 / 10, altText:
  "Coverage rings per condition: green where two or more modalities reach the required range, amber for one, red for none." });
s.addText([
  { text: "Clear day and night: ", options: { bold: true } },
  { text: "2+ modalities on every bearing", options: { bold: true, color: GOOD } },
  { text: " (night: 5° straight behind on lidar alone)", options: { breakLine: true } },
  { text: "Fog: ", options: { bold: true } },
  { text: "nothing reaches 253 m ahead", options: { bold: true, color: BAD } },
  { text: " (radar 239 m, lidar 114 m); 1° behind on the camera alone. Snow: the camera alone ahead", options: { breakLine: true } },
  { text: "Near field: ", options: { bold: true } },
  { text: "cameras alone", options: { bold: true, color: WARN } },
  { text: "; lidar and radar are blind below 0.2–0.3 m and beside the doors" },
], body({ x: 0.6, y: 4.4, w: 8.8, h: 0.95, fontSize: 12, paraSpaceAfter: 3 }));
s.addNotes(notes.coverage);

// ---- 5. Level 5
s = pres.addSlide({ masterName: "CONTENT" });
s.addText("Is Level 5 possible today? No. Level 4 in city + highway: yes", { placeholder: "title" });
s.addImage({ path: FIG("safe_speed_fog.png"), x: 0.3, y: 1.0, w: 5.3, h: 5.3 * 4.0 / 6.4, altText:
  "Highest safe speed against fog visibility: 84 km/h at 200 m, about 66 km/h at 50 to 100 m, falling below 50 km/h under 30 m." });
const V = (a, b, c, bold) => [cell(a), cell(b, { align: "right", bold: bold[0] }), cell(c, { align: "right", bold: bold[1] })];
s.addTable(table([
  [head("km/h, 2 modalities"), head("car", { align: "right" }), head("pedestrian", { align: "right" })],
  V("clear day", "142", "124", [false, false]),
  V("night, unlit road", "142", "78", [false, true]),
  V("fog, 200 m visibility", "84", "77", [true, true]),
  V("snow", "124", "98", [false, false]),
]), { x: 5.85, y: 1.0, w: 3.8, colW: [2.0, 0.7, 1.1], rowH: 0.3 });
s.addText([
  { text: "L5 means no limit on roads or weather. Physics sets one: in fog and snow the car must slow, like a careful driver.",
    options: { bullet: true, breakLine: true } },
  { text: "No datasheet covers a sensor blocked by snow, ice or spray.", options: { bullet: true, breakLine: true } },
  { text: "Rare events need billions of test km (RAND 2016); law approves only defined domains (UNECE R157, German L4 law 2021).",
    options: { bullet: true } },
], body({ x: 5.85, y: 2.75, w: 3.85, h: 2.4, fontSize: 12, paraSpaceAfter: 6 }));
s.addNotes(notes.l5);

// ---- 6. summary
s = pres.addSlide({ masterName: "DARK" });
s.addText("Summary", body({ x: 0.6, y: 0.35, w: 8.8, h: 0.55, fontSize: 24, bold: true, color: "FFFFFF" }));
const stats = [["20", "sensors for 10,986 USD"], ["360°", "2+ modalities at car and pedestrian range, day and night"],
  ["84 km/h", "top speed in 200 m fog"]];
stats.forEach(([n, l], i) => {
  s.addText(n, body({ x: 0.6 + i * 3.0, y: 1.1, w: 2.8, h: 0.85, fontSize: 44, bold: true, color: "FFFFFF" }));
  s.addText(l, body({ x: 0.6 + i * 3.0, y: 1.95, w: 2.6, h: 0.6, fontSize: 13, color: LIGHT }));
});
s.addText([
  { text: "Compare: ", options: { bold: true, bullet: true } },
  { text: "each modality has a blind axis; the spider charts come from one physics model.", options: { breakLine: true } },
  { text: "Design: ", options: { bold: true, bullet: true } },
  { text: "every sensor is there because a required range asks for it.", options: { breakLine: true } },
  { text: "Verdict: ", options: { bold: true, bullet: true } },
  { text: "Level 4 in city + highway inside a speed envelope. True Level 5 is not possible today.", options: { breakLine: true } },
  { text: "Next: ", options: { bold: true, bullet: true } },
  { text: "ultrasonic ring (near field), a rear radar (straight behind), longer-range imaging radar (fog ahead)." },
], body({ x: 0.6, y: 2.95, w: 8.8, h: 2.3, fontSize: 14, color: "FFFFFF", paraSpaceAfter: 6 }));
s.addNotes(notes.summary);

// Write, then repack without folder entries (cloud importers such as Google Slides can choke on them).
const fs = require("fs");
const JSZip = require("jszip");
const out = path.join(__dirname, "pitch.pptx");
pres.writeFile({ fileName: out }).then(async () => {
  const src = await JSZip.loadAsync(fs.readFileSync(out));
  const dst = new JSZip();
  for (const [name, entry] of Object.entries(src.files)) {
    if (!entry.dir) dst.file(name, await entry.async("nodebuffer"), { createFolders: false });
  }
  fs.writeFileSync(out, await dst.generateAsync({ type: "nodebuffer", compression: "DEFLATE", createFolders: false }));
  console.log("wrote " + out);
});

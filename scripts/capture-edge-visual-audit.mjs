import { chromium } from "../.browser-tools/node_modules/playwright-core/index.mjs";
import { mkdir } from "node:fs/promises";
const edge="C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",url="https://cintiabot.todosobreall.tech/transport-3d.html?quality=ultra",output="edge-visual-audit";
await mkdir(output,{recursive:true});
const browser=await chromium.launch({executablePath:edge,headless:false,args:["--use-angle=d3d11","--start-maximized"]});
const page=await browser.newPage({viewport:{width:1600,height:900},deviceScaleFactor:1});
const errors=[];page.on("pageerror",error=>errors.push(error.message));page.on("console",message=>{if(message.type()==="error")errors.push(message.text())});
await page.goto(url,{waitUntil:"networkidle",timeout:60000});await page.waitForTimeout(5000);
const enter=page.locator("[data-enter]");if(await enter.isVisible())await enter.click();await page.waitForTimeout(1200);
for(let camera=1;camera<=9;camera++){await page.keyboard.press(String(camera));await page.waitForTimeout(900);await page.screenshot({path:`${output}/camera-${camera}.png`})}
await page.keyboard.press("1");await page.waitForTimeout(600);await page.locator(".dock-tab").first().click();
for(const item of [{id:"truck",name:"truck"},{id:"bus",name:"bus"},{id:"ambulance",name:"ambulance"},{id:"fireEngine",name:"fire"},{id:"recoveryTruck",name:"recovery"}]){const control=page.locator(`#${item.id}`);if(await control.count()){await control.click();await page.waitForTimeout(1300);await page.keyboard.press("1");await page.screenshot({path:`${output}/vehicle-${item.name}-exterior.png`});await page.keyboard.press("2");await page.waitForTimeout(700);await page.screenshot({path:`${output}/vehicle-${item.name}-interior.png`});await page.keyboard.press("1")}}
console.log(JSON.stringify({captures:19,errors:[...new Set(errors)]},null,2));
await page.waitForTimeout(5000);await browser.close();

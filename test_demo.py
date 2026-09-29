"""
Exercises the demo the way the client will: drag the slider, switch language,
attach photos, remove one, submit empty, submit valid. Screenshots at each
step so the result is looked at, not just asserted.
"""
import sys
from playwright.sync_api import sync_playwright

import os
URL = "http://127.0.0.1:" + os.environ["PORT"] + "/index.html"
SHOT = "/var/lib/freelancer/projects/40739456/demo/shots/"
IMG = "/var/lib/freelancer/projects/40739456/demo/images/"

fails = []


def check(label, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + label + (" :: " + detail if detail else ""))
    if not cond:
        fails.append(label + (" :: " + detail if detail else ""))


def pos(page):
    """Current divider position, as the browser has computed it."""
    return page.evaluate(
        "getComputedStyle(document.getElementById('cmp'))"
        ".getPropertyValue('--pos').trim()"
    )


with sync_playwright() as p:
    browser = p.chromium.launch(args=["--no-proxy-server"])
    page = browser.new_page(viewport={"width": 1280, "height": 720})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append("console." + m.type + ": " + m.text)
            if m.type == "error" else None)

    page.goto(URL, wait_until="load")
    page.wait_for_timeout(400)
    page.screenshot(path=SHOT + "01-desktop-top.png")

    # Structural guard: a data-i18n element is rewritten with textContent, so
    # nesting another translatable node inside one silently deletes it.
    print("\nMarkup")
    nested = page.evaluate("""() =>
      [...document.querySelectorAll('[data-i18n]')]
        .filter(el => el.querySelector('[data-i18n]'))
        .map(el => el.tagName + '[' + el.dataset.i18n + ']')""")
    check("no data-i18n element contains another", not nested, "; ".join(nested))

    check("optional hint survives first render",
          page.locator("label[for=email] .opt").inner_text().strip() != "",
          "'" + page.locator("label[for=email]").inner_text().strip() + "'")

    # ---- slider -----------------------------------------------------
    print("\nComparison slider")
    check("starts centred", pos(page) == "50%", pos(page))

    # Scroll it fully into view first. The container is 625px tall in a 720px
    # viewport, so its centre sits below the fold on load and raw mouse
    # coordinates would land off-screen and hit nothing.
    page.locator("#cmp").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    box = page.locator("#cmp").bounding_box()
    check("slider centre is on-screen",
          box["y"] + box["height"] * 0.5 < 720,
          "centre y=" + str(round(box["y"] + box["height"] * 0.5)))

    page.mouse.move(box["x"] + box["width"] * 0.5, box["y"] + box["height"] * 0.5)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.18, box["y"] + box["height"] * 0.5, steps=12)
    page.mouse.up()
    page.wait_for_timeout(150)
    dragged = float(pos(page).rstrip("%"))
    check("drag moves the divider left", 10 < dragged < 26, pos(page))
    page.screenshot(path=SHOT + "02-slider-dragged.png")

    # the AFTER frame must actually be clipped, not just the divider moved
    clip = page.evaluate(
        "getComputedStyle(document.querySelector('#cmp .after')).clipPath"
    )
    check("after frame is clipped to the divider", "inset" in clip, clip)

    # Caption fade, driven to each extreme rather than relying on where a
    # drag happened to stop: a label must vanish before the divider reaches it.
    def set_slider(v):
        page.evaluate(
            "v => { const r = document.getElementById('cmpRange');"
            "r.value = v; r.dispatchEvent(new Event('input')); }", v)
        page.wait_for_timeout(200)

    def opacity(sel):
        return page.locator(sel).evaluate("e => getComputedStyle(e).opacity")

    set_slider(3)
    check("left caption hides when the divider reaches it",
          opacity("#cmp .tag.l") == "0", opacity("#cmp .tag.l"))
    check("right caption stays visible at the left extreme",
          opacity("#cmp .tag.r") == "1", opacity("#cmp .tag.r"))
    page.screenshot(path=SHOT + "02b-slider-far-left.png")

    set_slider(97)
    check("right caption hides at the right extreme",
          opacity("#cmp .tag.r") == "0", opacity("#cmp .tag.r"))
    check("left caption stays visible at the right extreme",
          opacity("#cmp .tag.l") == "1", opacity("#cmp .tag.l"))
    set_slider(50)

    # keyboard
    page.locator("#cmpRange").focus()
    before_kb = float(pos(page).rstrip("%"))
    for _ in range(5):
        page.keyboard.press("ArrowRight")
    page.wait_for_timeout(120)
    check("arrow keys move the divider",
          float(pos(page).rstrip("%")) > before_kb,
          str(before_kb) + " -> " + pos(page))

    # click-to-jump
    page.mouse.click(box["x"] + box["width"] * 0.8, box["y"] + box["height"] * 0.5)
    page.wait_for_timeout(120)
    check("tapping the photo jumps the divider",
          float(pos(page).rstrip("%")) > 70, pos(page))

    # ---- validation -------------------------------------------------
    print("\nValidation (empty submit)")
    page.locator("button.submit").click()
    page.wait_for_timeout(200)
    shown = page.locator(".err:not(:empty)").count()
    check("empty submit raises errors", shown >= 4, str(shown) + " messages")
    check("result panel stays hidden", page.locator("#result").is_hidden())
    check("first bad field takes focus",
          page.evaluate("document.activeElement.id") == "name",
          page.evaluate("document.activeElement.id"))
    page.locator("#name").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(path=SHOT + "03-validation-en.png")

    # short description is rejected separately from an empty one
    page.fill("#desc", "dent")
    page.locator("button.submit").click()
    page.wait_for_timeout(150)
    check("too-short description is caught",
          "10" in page.locator('[data-err="desc"]').inner_text(),
          page.locator('[data-err="desc"]').inner_text())

    # bad email
    page.fill("#email", "not-an-email")
    page.locator("button.submit").click()
    page.wait_for_timeout(150)
    check("bad email is caught",
          page.locator('[data-err="email"]').inner_text() != "")

    # ---- uploads ----------------------------------------------------
    print("\nPhoto upload")
    page.set_input_files("#photos", [IMG + "demo-before.jpg", IMG + "demo-after.jpg"])
    page.wait_for_timeout(500)
    check("two thumbnails render", page.locator(".thumb").count() == 2,
          str(page.locator(".thumb").count()))
    check("thumbnail shows the filename",
          "demo-before.jpg" in page.locator(".thumb .name").first.inner_text())

    # a non-image must be refused by name/type
    page.set_input_files("#photos", [__file__])
    page.wait_for_timeout(300)
    check("non-image is rejected",
          "isn't an image" in page.locator('[data-err="photos"]').inner_text(),
          page.locator('[data-err="photos"]').inner_text())
    check("rejected file adds no thumbnail", page.locator(".thumb").count() == 2)

    # removing one
    page.locator(".thumb button").first.click()
    page.wait_for_timeout(200)
    check("remove button drops one thumbnail", page.locator(".thumb").count() == 1,
          str(page.locator(".thumb").count()))

    page.set_input_files("#photos", [IMG + "demo-before.jpg"])
    page.wait_for_timeout(400)

    # ---- valid submit -----------------------------------------------
    print("\nValid submit")
    page.fill("#name", "Maria Delgado")
    page.fill("#phone", "555 0134 998")
    page.fill("#email", "maria@example.com")
    page.select_option("#year", "2019")
    page.fill("#makemodel", "Honda Civic")
    page.select_option("#service", index=1)
    page.fill("#desc", "Rear quarter panel scraped along a wall in the parking garage.")
    page.locator("button.submit").click()
    page.wait_for_timeout(400)

    check("result panel appears", page.locator("#result").is_visible())
    body = page.locator("#resultBody").inner_text()
    check("result carries the vehicle", "2019 Honda Civic" in body, body[:120])
    check("result lists both photos",
          body.count("demo-before.jpg") + body.count("demo-after.jpg") == 2, body[:220])
    check("no errors remain", page.locator(".err:not(:empty)").count() == 0)
    page.locator("#result").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(path=SHOT + "04-submitted-en.png")

    # ---- Spanish ----------------------------------------------------
    print("\nSpanish")
    page.locator('.lang button[data-lang="es"]').click()
    page.wait_for_timeout(350)
    check("html lang flips", page.get_attribute("html", "lang") == "es")
    check("heading translates",
          "Antes y después" in page.locator("h1").inner_text(),
          page.locator("h1").inner_text())
    check("button translates",
          page.locator("button.submit").inner_text().strip() == "Enviar solicitud",
          page.locator("button.submit").inner_text())
    # .tag is text-transform:uppercase, and inner_text() returns the RENDERED
    # text, so compare case-insensitively rather than against the source string.
    check("slider captions translate",
          page.locator("#cmp .tag.r").inner_text().strip().lower() == "antes",
          page.locator("#cmp .tag.r").inner_text())
    check("service options translate",
          "Reparación de colisión" in page.locator("#service").inner_text(),
          page.locator("#service").inner_text()[:80])
    check("year selection survives the language switch",
          page.input_value("#year") == "2019", page.input_value("#year"))
    check("typed text is not wiped",
          page.input_value("#makemodel") == "Honda Civic")
    check("photos survive the language switch",
          page.locator(".thumb").count() == 2, str(page.locator(".thumb").count()))
    check("optional hint is translated, not lost",
          page.locator("label[for=email] .opt").inner_text().strip() == "(opcional)",
          "'" + page.locator("label[for=email]").inner_text().strip() + "'")

    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(250)
    page.screenshot(path=SHOT + "05-spanish-top.png")

    # errors must come back in Spanish
    page.fill("#name", "")
    page.fill("#desc", "")
    page.locator("button.submit").click()
    page.wait_for_timeout(250)
    check("errors are in Spanish",
          "Por favor" in page.locator('[data-err="name"]').inner_text(),
          page.locator('[data-err="name"]').inner_text())
    page.locator("#name").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(path=SHOT + "06-validation-es.png")

    # ---- mobile -----------------------------------------------------
    print("\nMobile 390x844")
    m = browser.new_page(viewport={"width": 390, "height": 844},
                         is_mobile=True, has_touch=True,
                         device_scale_factor=2)
    m.goto(URL, wait_until="load")
    m.wait_for_timeout(500)
    overflow = m.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth")
    check("no horizontal overflow on mobile", overflow <= 0, "overflow " + str(overflow))

    # every element must sit inside the viewport, not just the document
    spill = m.evaluate("""() => {
      const w = document.documentElement.clientWidth, out = [];
      document.querySelectorAll('body *').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.width && (r.left < -1 || r.right > w + 1))
          out.push(el.tagName + '.' + el.className + ' ' + Math.round(r.left)
                   + '..' + Math.round(r.right));
      });
      return out.slice(0, 6);
    }""")
    check("nothing spills past the viewport", not spill, "; ".join(spill))
    m.screenshot(path=SHOT + "07-mobile-top.png")

    mbox = m.locator("#cmp").bounding_box()
    m.touchscreen.tap(mbox["x"] + mbox["width"] * 0.25, mbox["y"] + mbox["height"] * 0.5)
    m.wait_for_timeout(200)
    mpos = m.evaluate("getComputedStyle(document.getElementById('cmp'))"
                      ".getPropertyValue('--pos').trim()")
    check("slider responds to touch", float(mpos.rstrip("%")) < 40, mpos)

    m.locator("#estimate").scroll_into_view_if_needed()
    m.wait_for_timeout(300)
    m.screenshot(path=SHOT + "08-mobile-form.png")

    check("no JS errors", not errors, " | ".join(errors[:4]))

    browser.close()

print("\n" + ("ALL PASSED" if not fails else "FAILURES:\n- " + "\n- ".join(fails)))
sys.exit(1 if fails else 0)

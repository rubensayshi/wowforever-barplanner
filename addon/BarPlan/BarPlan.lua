-- BarPlan: applies a plan made in the bar planner page (index.html).
-- Paste the plan string into /barplan and press Apply. It
--   * creates or updates the plan's macros (matched by name),
--   * puts spells, macros and items into the planned action slots,
--   * binds the planned keys to the planned buttons and saves the bindings.
-- Slots and buttons that are not in the plan are left alone.
--
-- EllesmereUI's action bars show the game's normal action slots and use the
-- game's normal button bindings (ACTIONBUTTON1, MULTIACTIONBAR1BUTTON1, ...),
-- so whatever this addon sets shows up on those bars.
--
-- The last applied plan is kept in BarPlanDB. With auto-fill on (the default),
-- a spell you learn later goes into its planned slot if that slot is empty.

BarPlan = BarPlan or {}
local BP = BarPlan

local PREFIX = "BP1:"
local FORMAT_VERSION = 1
local DEFAULT_ICON = "INV_Misc_QuestionMark"
local MACRO_BODY_MAX = 255

------------------------------------------------------------------------
-- Bars, slots and binding commands (same tables as index.html)
------------------------------------------------------------------------

-- first = first action slot of the bar, bind = binding command prefix
local PAGES = {
    { first = 1,   label = "Bar 1",          bind = "ACTIONBUTTON" },
    { first = 61,  label = "Bar 2",          bind = "MULTIACTIONBAR1BUTTON" },
    { first = 49,  label = "Bar 3",          bind = "MULTIACTIONBAR2BUTTON" },
    { first = 25,  label = "Bar 4",          bind = "MULTIACTIONBAR3BUTTON" },
    { first = 37,  label = "Bar 5",          bind = "MULTIACTIONBAR4BUTTON" },
    { first = 145, label = "Bar 6",          bind = "MULTIACTIONBAR5BUTTON" },
    { first = 157, label = "Bar 7",          bind = "MULTIACTIONBAR6BUTTON" },
    { first = 169, label = "Bar 8",          bind = "MULTIACTIONBAR7BUTTON" },
    { first = 73,  label = "Bar 1 stance 1" },
    { first = 85,  label = "Bar 1 stance 2" },
    { first = 97,  label = "Bar 1 stance 3" },
    { first = 109, label = "Bar 1 stance 4" },
}

-- Non-bar commands the planner offers under "Other keybinds".
local OTHER_COMMANDS = {
    "MOVEFORWARD", "MOVEBACKWARD", "TURNLEFT", "TURNRIGHT", "STRAFELEFT", "STRAFERIGHT",
    "JUMP", "TOGGLEAUTORUN", "SITORSTAND", "TOGGLESHEATH",
    "TARGETNEARESTENEMY", "TARGETPREVIOUSENEMY", "TARGETNEARESTFRIEND", "ASSISTTARGET",
    "INTERACTTARGET", "TARGETSELF", "TARGETPARTYMEMBER1", "TARGETPARTYMEMBER2",
    "TARGETPARTYMEMBER3", "TARGETPARTYMEMBER4", "OPENALLBAGS", "TOGGLEWORLDMAP",
}

local function slotLabel(slot)
    for _, p in ipairs(PAGES) do
        if slot >= p.first and slot < p.first + 12 then
            return p.label .. " button " .. (slot - p.first + 1)
        end
    end
    return "slot " .. slot
end

local function allCommands()
    local list = {}
    for _, p in ipairs(PAGES) do
        if p.bind then
            for i = 1, 12 do list[#list + 1] = p.bind .. i end
        end
    end
    for i = 1, 10 do list[#list + 1] = "SHAPESHIFTBUTTON" .. i end -- stance bar
    for i = 1, 10 do list[#list + 1] = "BONUSACTIONBUTTON" .. i end -- pet bar
    for _, c in ipairs(OTHER_COMMANDS) do list[#list + 1] = c end
    return list
end

------------------------------------------------------------------------
-- Plan string: "BP1:" + base64 of UTF-8 text, one record per line,
-- fields separated by tabs. Backslash, tab and newline inside a field
-- are written as \\, \t and \n.
--   BARPLAN <version>
--   CLASS   <WARRIOR, SHAMAN, ...> (optional; Apply refuses a plan for another class)
--   NAME    <plan name>
--   MACRO   <name> <icon> <0|1 per character> <body>
--   SLOT    <slot> <spell|macro|item|clear> <value>
--   BIND    <key> <command>
-- No WoW API is used in this section, so it can be tested outside the game.
------------------------------------------------------------------------

local B64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local B64DEC = {}
for i = 1, 64 do B64DEC[B64:byte(i)] = i - 1 end

function BP.b64encode(s)
    local out = {}
    for i = 1, #s, 3 do
        local a, b, c = s:byte(i, i + 2)
        local n = a * 65536 + (b or 0) * 256 + (c or 0)
        local c1 = math.floor(n / 262144) % 64
        local c2 = math.floor(n / 4096) % 64
        local c3 = math.floor(n / 64) % 64
        local c4 = n % 64
        out[#out + 1] = B64:sub(c1 + 1, c1 + 1) .. B64:sub(c2 + 1, c2 + 1)
            .. (b and B64:sub(c3 + 1, c3 + 1) or "=")
            .. (c and B64:sub(c4 + 1, c4 + 1) or "=")
    end
    return table.concat(out)
end

function BP.b64decode(s)
    local out = {}
    local bits, nbits = 0, 0
    for i = 1, #s do
        local v = B64DEC[s:byte(i)]
        if v then -- skips padding, spaces and line breaks
            bits = bits * 64 + v
            nbits = nbits + 6
            if nbits >= 8 then
                nbits = nbits - 8
                local p = 2 ^ nbits
                local byte = math.floor(bits / p)
                bits = bits - byte * p
                out[#out + 1] = string.char(byte)
            end
        end
    end
    return table.concat(out)
end

local UNESC = { n = "\n", t = "\t", ["\\"] = "\\" }
local function unesc(s)
    return ((s or ""):gsub("\\(.)", UNESC))
end

local function esc(s)
    s = tostring(s or "")
    s = s:gsub("\\", "\\\\")
    s = s:gsub("\t", "\\t")
    s = s:gsub("\r", "")
    s = s:gsub("\n", "\\n")
    return s
end

local function splitTabs(line)
    local t = {}
    for f in (line .. "\t"):gmatch("(.-)\t") do t[#t + 1] = f end
    return t
end

local function trim(s)
    return ((s or ""):gsub("^%s+", ""):gsub("%s+$", ""))
end

-- Returns plan or nil, error message.
function BP.parse(text)
    text = trim(text)
    if text == "" then return nil, "Paste a plan string first." end
    if text:sub(1, #PREFIX) ~= PREFIX then
        return nil, "That isn't a plan string. It should start with " .. PREFIX
    end
    local raw = BP.b64decode(text:sub(#PREFIX + 1))
    local plan = { name = "", macros = {}, slots = {}, binds = {} }
    local version
    for line in raw:gmatch("[^\n]+") do
        local f = splitTabs((line:gsub("\r$", "")))
        local kind = f[1]
        if kind == "BARPLAN" then
            version = tonumber(f[2])
        elseif kind == "CLASS" then
            plan.class = f[2]
        elseif kind == "NAME" then
            plan.name = unesc(f[2])
        elseif kind == "MACRO" and f[2] and f[2] ~= "" then
            plan.macros[#plan.macros + 1] = {
                name = unesc(f[2]), icon = unesc(f[3]), perChar = f[4] == "1", body = unesc(f[5]),
            }
        elseif kind == "SLOT" and tonumber(f[2]) and f[3] then
            plan.slots[#plan.slots + 1] = { slot = tonumber(f[2]), kind = f[3], value = trim(unesc(f[4])) }
        elseif kind == "BIND" and f[2] and f[2] ~= "" and f[3] and f[3] ~= "" then
            plan.binds[#plan.binds + 1] = { key = f[2], command = f[3] }
        end
    end
    if not version then
        return nil, "The plan string is damaged. Copy it again from the planner."
    end
    if version > FORMAT_VERSION then
        return nil, "This plan was made by a newer planner. Update the BarPlan addon."
    end
    return plan
end

function BP.serialize(plan)
    local lines = { "BARPLAN\t" .. FORMAT_VERSION }
    if plan.class then lines[#lines + 1] = "CLASS\t" .. plan.class end
    if plan.name and plan.name ~= "" then lines[#lines + 1] = "NAME\t" .. esc(plan.name) end
    for _, m in ipairs(plan.macros or {}) do
        lines[#lines + 1] = table.concat({ "MACRO", esc(m.name), esc(m.icon), m.perChar and "1" or "0", esc(m.body) }, "\t")
    end
    for _, s in ipairs(plan.slots or {}) do
        lines[#lines + 1] = table.concat({ "SLOT", s.slot, s.kind, esc(s.value) }, "\t")
    end
    for _, b in ipairs(plan.binds or {}) do
        lines[#lines + 1] = table.concat({ "BIND", b.key, b.command }, "\t")
    end
    return PREFIX .. BP.b64encode(table.concat(lines, "\n"))
end

-- Everything below needs the game client.
if not CreateFrame then return end

------------------------------------------------------------------------
-- Game API wrappers (Forever has a mix of old and new spell APIs)
------------------------------------------------------------------------

local BOOK = BOOKTYPE_SPELL or "spell"

local function say(msg)
    DEFAULT_CHAT_FRAME:AddMessage("|cff0cd29fBarPlan|r: " .. msg)
end

local function getSpellName(id)
    if C_Spell and C_Spell.GetSpellName then return C_Spell.GetSpellName(id) end
    if GetSpellInfo then return (GetSpellInfo(id)) end
end

local function getSpellSubtext(id)
    if C_Spell and C_Spell.GetSpellSubtext then return C_Spell.GetSpellSubtext(id) end
    if GetSpellSubtext then return GetSpellSubtext(id) end
end

local function getSpellIDByName(name)
    if C_Spell and C_Spell.GetSpellInfo then
        local info = C_Spell.GetSpellInfo(name)
        if info then return info.spellID end
    end
    if GetSpellInfo then return (select(7, GetSpellInfo(name))) end
end

local function pickupSpellID(id)
    if C_Spell and C_Spell.PickupSpell then C_Spell.PickupSpell(id)
    elseif PickupSpell then PickupSpell(id) end
end

local function isKnownSpell(id)
    return (IsPlayerSpell and IsPlayerSpell(id)) or (IsSpellKnown and IsSpellKnown(id)) or false
end

local function getItemName(id)
    if C_Item and C_Item.GetItemNameByID then return C_Item.GetItemNameByID(id) end
    if GetItemInfo then return (GetItemInfo(id)) end
end

local function getItemID(nameOrID)
    if C_Item and C_Item.GetItemInfoInstant then return (C_Item.GetItemInfoInstant(nameOrID)) end
    if GetItemInfoInstant then return (GetItemInfoInstant(nameOrID)) end
end

local function pickupItem(id)
    if C_Item and C_Item.PickupItem then C_Item.PickupItem(id) else PickupItem(id) end
end

local function useNewSpellBook()
    return C_SpellBook and C_SpellBook.GetSpellBookItemInfo and Enum and Enum.SpellBookSpellBank
end

-- Usable (non-passive) spells in the player's spellbook, in book order.
-- Ranks of a spell are listed lowest first, so the last match is the highest rank.
local function spellbookEntries()
    local count = 0
    if C_SpellBook and C_SpellBook.GetNumSpellBookSkillLines then
        for t = 1, C_SpellBook.GetNumSpellBookSkillLines() do
            local info = C_SpellBook.GetSpellBookSkillLineInfo(t)
            if info then count = math.max(count, (info.itemIndexOffset or 0) + (info.numSpellBookItems or 0)) end
        end
    elseif GetNumSpellTabs then
        for t = 1, GetNumSpellTabs() do
            local _, _, offset, num = GetSpellTabInfo(t)
            count = math.max(count, (offset or 0) + (num or 0))
        end
    end
    local list = {}
    for i = 1, count do
        local name, rank, spellID, usable
        if useNewSpellBook() then
            local info = C_SpellBook.GetSpellBookItemInfo(i, Enum.SpellBookSpellBank.Player)
            if info and info.name then
                name, rank, spellID = info.name, info.subName, info.spellID
                usable = info.itemType == Enum.SpellBookItemType.Spell and not info.isPassive
            end
        else
            name, rank, spellID = GetSpellBookItemName(i, BOOK)
            local kind = GetSpellBookItemInfo and GetSpellBookItemInfo(i, BOOK)
            usable = name and kind == "SPELL" and not (IsPassiveSpell and IsPassiveSpell(i, BOOK))
        end
        if usable then
            list[#list + 1] = { index = i, name = name, rank = rank or "", spellID = spellID }
        end
    end
    return list
end

local function pickupBookEntry(e)
    if useNewSpellBook() and C_SpellBook.PickupSpellBookItem then
        C_SpellBook.PickupSpellBookItem(e.index, Enum.SpellBookSpellBank.Player)
    elseif PickupSpellBookItem then
        PickupSpellBookItem(e.index, BOOK)
    end
    if not GetCursorInfo() and e.spellID then pickupSpellID(e.spellID) end
end

-- value: "Lightning Bolt", "Healing Wave(Rank 1)" or "spell:403".
-- Returns { kind, id, pickup } or nil, reason.
local function resolveSpell(value, book)
    local id = tonumber(value:match("^spell:(%d+)$"))
    if id then
        if not isKnownSpell(id) then return nil, "not learned yet" end
        return { kind = "spell", id = id, pickup = function() pickupSpellID(id) end }
    end
    local base, rank = value:match("^(.-)%s*%(([^()]*)%)$")
    base = (base or value):lower()
    rank = rank and trim(rank):lower()
    local found
    for _, e in ipairs(book) do
        if e.name:lower() == base and (not rank or e.rank:lower() == rank) then found = e end
    end
    if found then
        return { kind = "spell", id = found.spellID, pickup = function() pickupBookEntry(found) end }
    end
    if rank then
        local rid = getSpellIDByName(value)
        if rid and isKnownSpell(rid) then
            return { kind = "spell", id = rid, pickup = function() pickupSpellID(rid) end }
        end
        return nil, "that rank isn't in your spellbook (turn on Show All Spell Ranks)"
    end
    return nil, "not learned yet"
end

local function resolveItem(value)
    local id = tonumber(value:match("^item:(%d+)")) or tonumber(value) or getItemID(value)
    if not id then return nil, "item not found; have it in your bags and try again" end
    return { kind = "item", id = id, pickup = function() pickupItem(id) end }
end

local function resolveMacro(value)
    local idx = GetMacroIndexByName(value)
    if not idx or idx == 0 then return nil, "no macro with that name" end
    return { kind = "macro", id = idx, pickup = function() PickupMacro(idx) end }
end

local function slotHolds(slot, target)
    local kind, id = GetActionInfo(slot)
    return kind == target.kind and id == target.id
end

local function placeTarget(slot, target)
    ClearCursor()
    target.pickup()
    if not GetCursorInfo() then return false end
    PlaceAction(slot)
    ClearCursor()
    return HasAction(slot)
end

------------------------------------------------------------------------
-- Applying a plan
------------------------------------------------------------------------

local function applyMacros(plan, dry, r)
    local nAccount, nChar = GetNumMacros()
    local maxAccount = MAX_ACCOUNT_MACROS or 120
    local maxChar = MAX_CHARACTER_MACROS or 18
    for _, m in ipairs(plan.macros) do
        if #m.body > MACRO_BODY_MAX then
            r.problems[#r.problems + 1] = ("Macro %s is %d characters; the game keeps the first %d.")
                :format(m.name, #m.body, MACRO_BODY_MAX)
        end
        local icon = tonumber(m.icon) or (m.icon ~= "" and m.icon) or nil
        local idx = GetMacroIndexByName(m.name)
        if idx and idx > 0 then
            local _, oldIcon, oldBody = GetMacroInfo(idx)
            if trim(oldBody) == trim(m.body) then
                r.macrosSame = r.macrosSame + 1
            else
                if not dry then EditMacro(idx, m.name, icon or oldIcon, m.body) end
                r.macrosChanged = r.macrosChanged + 1
            end
        elseif m.perChar and nChar >= maxChar then
            r.problems[#r.problems + 1] = "Macro " .. m.name .. ": character macros are full (" .. maxChar .. ")."
        elseif not m.perChar and nAccount >= maxAccount then
            r.problems[#r.problems + 1] = "Macro " .. m.name .. ": general macros are full (" .. maxAccount .. ")."
        else
            local ok, res = true, true
            if not dry then ok, res = pcall(CreateMacro, m.name, icon or DEFAULT_ICON, m.body, m.perChar) end
            if ok and res then
                r.macrosNew = r.macrosNew + 1
                if m.perChar then nChar = nChar + 1 else nAccount = nAccount + 1 end
            else
                r.problems[#r.problems + 1] = "Macro " .. m.name .. ": couldn't create it (" .. tostring(res) .. ")."
            end
        end
    end
end

local function applySlots(plan, dry, r)
    local planMacros = {}
    for _, m in ipairs(plan.macros) do planMacros[m.name:lower()] = true end
    local book = spellbookEntries()
    for _, s in ipairs(plan.slots) do
        local label = slotLabel(s.slot)
        if s.kind == "clear" then
            if HasAction(s.slot) then
                if not dry then PickupAction(s.slot); ClearCursor() end
                r.cleared = r.cleared + 1
            end
        else
            local target, why
            if s.kind == "spell" then
                target, why = resolveSpell(s.value, book)
            elseif s.kind == "macro" then
                target, why = resolveMacro(s.value)
                if not target and dry and planMacros[s.value:lower()] then
                    target = { kind = "macro", id = -1 } -- created by Apply
                end
            elseif s.kind == "item" then
                target, why = resolveItem(s.value)
            else
                why = "unknown slot type " .. tostring(s.kind)
            end
            if not target and why == "not learned yet" then
                r.notLearned[#r.notLearned + 1] = s.value
            elseif not target then
                r.skipped[#r.skipped + 1] = label .. ": " .. s.value .. " (" .. why .. ")"
            elseif slotHolds(s.slot, target) then
                r.same = r.same + 1
            elseif dry then
                r.placed = r.placed + 1
            elseif placeTarget(s.slot, target) then
                r.placed = r.placed + 1
            else
                r.problems[#r.problems + 1] = label .. ": couldn't place " .. s.value .. "."
            end
        end
    end
end

local function applyBinds(plan, dry, r)
    if #plan.binds == 0 then return end
    local changed = {}
    for _, b in ipairs(plan.binds) do
        if GetBindingAction(b.key) ~= b.command then changed[#changed + 1] = b end
    end
    if dry then
        r.bound = #changed
        r.bindsSame = #plan.binds - #changed
        return
    end
    -- Take the old keys off every planned command first, so each planned
    -- button ends up with exactly the planned key.
    local cmds = {}
    for _, b in ipairs(plan.binds) do cmds[b.command] = true end
    for cmd in pairs(cmds) do
        local keys = { GetBindingKey(cmd) }
        for _, k in ipairs(keys) do SetBinding(k) end
    end
    for _, b in ipairs(plan.binds) do
        SetBinding(b.key, b.command)
        if GetBindingAction(b.key) ~= b.command then
            r.problems[#r.problems + 1] = "Key " .. b.key .. ": the game didn't accept it."
        end
    end
    r.bound = #changed
    r.bindsSame = #plan.binds - #changed
    SaveBindings(GetCurrentBindingSet())
end

function BP.apply(plan, dry)
    local r = {
        placed = 0, same = 0, cleared = 0, macrosNew = 0, macrosChanged = 0, macrosSame = 0,
        bound = 0, bindsSame = 0, notLearned = {}, skipped = {}, problems = {},
    }
    applyMacros(plan, dry, r)
    applySlots(plan, dry, r)
    applyBinds(plan, dry, r)
    ClearCursor()
    return r
end

local function reportLines(r, dry)
    local lines = {}
    if dry then
        lines[1] = ("Check: %d slots to fill, %d already right, %d to clear. Macros: %d new, %d changed, %d unchanged. Keys: %d to set, %d already set.")
            :format(r.placed, r.same, r.cleared, r.macrosNew, r.macrosChanged, r.macrosSame, r.bound, r.bindsSame)
    else
        lines[1] = ("Done: %d slots filled, %d already right, %d cleared. Macros: %d new, %d changed. Keys: %d set.")
            :format(r.placed, r.same, r.cleared, r.macrosNew, r.macrosChanged, r.bound)
    end
    if #r.notLearned > 0 then
        lines[#lines + 1] = ("Not learned yet, skipped (%d): %s"):format(#r.notLearned, table.concat(r.notLearned, ", "))
    end
    for _, s in ipairs(r.skipped) do lines[#lines + 1] = "Skipped " .. s end
    for _, p in ipairs(r.problems) do lines[#lines + 1] = "|cffff6060" .. p .. "|r" end
    return lines
end

------------------------------------------------------------------------
-- Export: turn the current bars and keys into a plan string
------------------------------------------------------------------------

function BP.exportCurrent()
    local _, class = UnitClass("player")
    local plan = { name = (UnitName("player") or "?") .. " (from game)", class = class, macros = {}, slots = {}, binds = {} }
    local book = spellbookEntries()
    local seenMacro = {}
    local maxAccount = MAX_ACCOUNT_MACROS or 120
    for _, p in ipairs(PAGES) do
        for i = 0, 11 do
            local slot = p.first + i
            if HasAction(slot) then
                local kind, id = GetActionInfo(slot)
                if kind == "spell" then
                    local name = getSpellName(id)
                    if name then
                        -- Keep the rank only when it isn't the highest one you know.
                        local best = resolveSpell(name, book)
                        local sub = getSpellSubtext(id)
                        if best and best.id ~= id and sub and sub ~= "" then name = name .. "(" .. sub .. ")" end
                        plan.slots[#plan.slots + 1] = { slot = slot, kind = "spell", value = name }
                    end
                elseif kind == "macro" then
                    local name, icon, body = GetMacroInfo(id)
                    if name then
                        plan.slots[#plan.slots + 1] = { slot = slot, kind = "macro", value = name }
                        if not seenMacro[name] then
                            seenMacro[name] = true
                            plan.macros[#plan.macros + 1] = {
                                name = name, icon = tostring(icon or ""), perChar = id > maxAccount, body = body or "",
                            }
                        end
                    end
                elseif kind == "item" then
                    plan.slots[#plan.slots + 1] = { slot = slot, kind = "item", value = getItemName(id) or ("item:" .. id) }
                end
            end
        end
    end
    for _, cmd in ipairs(allCommands()) do
        local key = GetBindingKey(cmd)
        if key then plan.binds[#plan.binds + 1] = { key = key, command = cmd } end
    end
    return BP.serialize(plan)
end

------------------------------------------------------------------------
-- Window
------------------------------------------------------------------------

local frame

local function showStatus(lines)
    for _, l in ipairs(lines) do say(l) end
    if not frame then return end
    local shown = {}
    for i = 1, math.min(#lines, 6) do shown[i] = lines[i] end
    if #lines > 6 then shown[#shown + 1] = "... " .. (#lines - 6) .. " more lines in chat." end
    frame.status:SetText(table.concat(shown, "\n"))
end

function BP.run(text, dry)
    if InCombatLockdown() then
        showStatus({ "Can't change bars or keys in combat. Try again after the fight." })
        return
    end
    local plan, err = BP.parse(text)
    if not plan then
        showStatus({ err })
        return
    end
    local _, myClass = UnitClass("player")
    if plan.class and myClass and plan.class ~= myClass then
        showStatus({ ("This plan is for a %s and this character is a %s. Switch class in the planner and copy that plan.")
            :format(plan.class:lower(), myClass:lower()) })
        return
    end
    local r = BP.apply(plan, dry)
    if not dry then BarPlanDB.last = trim(text) end
    showStatus(reportLines(r, dry))
end

local function buildFrame()
    local f = CreateFrame("Frame", "BarPlanFrame", UIParent, "BasicFrameTemplateWithInset")
    f:SetSize(620, 470)
    f:SetPoint("CENTER")
    f:SetFrameStrata("DIALOG")
    f:SetClampedToScreen(true)
    f:SetMovable(true)
    f:EnableMouse(true)
    f:RegisterForDrag("LeftButton")
    f:SetScript("OnDragStart", f.StartMoving)
    f:SetScript("OnDragStop", f.StopMovingOrSizing)
    tinsert(UISpecialFrames, "BarPlanFrame") -- Esc closes it

    local title = f:CreateFontString(nil, "OVERLAY", "GameFontHighlight")
    title:SetPoint("TOP", 0, -5)
    title:SetText("BarPlan")

    local help = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    help:SetPoint("TOPLEFT", 16, -34)
    help:SetPoint("TOPRIGHT", -16, -34)
    help:SetJustifyH("LEFT")
    help:SetText("Paste a plan string from the bar planner page (Ctrl+V). Check shows what would change, Apply does it.")

    local scroll = CreateFrame("ScrollFrame", "BarPlanScroll", f, "UIPanelScrollFrameTemplate")
    scroll:SetPoint("TOPLEFT", 18, -56)
    scroll:SetPoint("BOTTOMRIGHT", -38, 150)

    local bg = f:CreateTexture(nil, "BACKGROUND", nil, 1)
    bg:SetPoint("TOPLEFT", scroll, -4, 4)
    bg:SetPoint("BOTTOMRIGHT", scroll, 4, -4)
    bg:SetColorTexture(0, 0, 0, 0.6)

    local edit = CreateFrame("EditBox", nil, scroll)
    edit:SetMultiLine(true)
    edit:SetAutoFocus(false)
    edit:SetFontObject(ChatFontNormal)
    edit:SetWidth(560)
    edit:SetMaxLetters(0)
    if edit.SetMaxBytes then edit:SetMaxBytes(0) end
    edit:SetScript("OnEscapePressed", edit.ClearFocus)
    scroll:SetScrollChild(edit)
    scroll:EnableMouse(true)
    scroll:SetScript("OnMouseDown", function() edit:SetFocus() end)
    f.edit = edit

    local status = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
    status:SetPoint("TOPLEFT", scroll, "BOTTOMLEFT", 0, -12)
    status:SetPoint("BOTTOMRIGHT", f, "BOTTOMRIGHT", -16, 46)
    status:SetJustifyH("LEFT")
    status:SetJustifyV("TOP")
    status:SetWordWrap(true)
    f.status = status

    local function button(text, x, width, onClick)
        local b = CreateFrame("Button", nil, f, "UIPanelButtonTemplate")
        b:SetSize(width, 24)
        b:SetPoint("BOTTOMLEFT", x, 14)
        b:SetText(text)
        b:SetScript("OnClick", onClick)
        return b
    end
    button("Check", 16, 90, function() edit:ClearFocus(); BP.run(edit:GetText(), true) end)
    button("Apply", 110, 90, function() edit:ClearFocus(); BP.run(edit:GetText(), false) end)
    button("Export my bars", 204, 130, function()
        edit:SetText(BP.exportCurrent())
        edit:SetFocus()
        edit:HighlightText()
        status:SetText("This is your current setup. Press Ctrl+C to copy it, then use Load in the planner.")
    end)
    button("Clear", 338, 70, function() edit:SetText(""); edit:SetFocus() end)

    local auto = CreateFrame("CheckButton", nil, f, "UICheckButtonTemplate")
    auto:SetSize(24, 24)
    auto:SetPoint("BOTTOMRIGHT", -150, 14)
    local autoLabel = f:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    autoLabel:SetPoint("LEFT", auto, "RIGHT", 2, 0)
    autoLabel:SetText("Auto-fill new spells")
    auto:SetChecked(BarPlanDB.auto)
    auto:SetScript("OnClick", function(self) BarPlanDB.auto = self:GetChecked() and true or false end)
    f.auto = auto

    f:Hide()
    return f
end

local function openFrame(text)
    frame = frame or buildFrame()
    frame.auto:SetChecked(BarPlanDB.auto)
    if text then frame.edit:SetText(text) end
    frame:Show()
end

------------------------------------------------------------------------
-- Auto-fill: when you learn a spell, put it in its planned slot if empty
------------------------------------------------------------------------

local autoQueued, autoAfterCombat = false, false

local function autoFill()
    autoQueued = false
    if not (BarPlanDB and BarPlanDB.auto and BarPlanDB.last) then return end
    if InCombatLockdown() then autoAfterCombat = true return end
    local plan = BP.parse(BarPlanDB.last)
    local _, myClass = UnitClass("player")
    if not plan or (plan.class and plan.class ~= myClass) then return end
    local book
    for _, s in ipairs(plan.slots) do
        if s.kind == "spell" and not HasAction(s.slot) then
            book = book or spellbookEntries()
            local target = resolveSpell(s.value, book)
            if target and placeTarget(s.slot, target) then
                say("Put " .. s.value .. " on " .. slotLabel(s.slot) .. ".")
            end
        end
    end
    ClearCursor()
end

local function queueAutoFill()
    if autoQueued then return end
    autoQueued = true
    C_Timer.After(1, autoFill)
end

local events = CreateFrame("Frame")
-- Not every client has every event (Classic Era has no LEARNED_SPELL_IN_TAB),
-- and registering an unknown one is an error that would stop the file here.
for _, ev in ipairs({ "ADDON_LOADED", "SPELLS_CHANGED", "LEARNED_SPELL_IN_TAB", "PLAYER_REGEN_ENABLED" }) do
    pcall(events.RegisterEvent, events, ev)
end
events:SetScript("OnEvent", function(_, event, arg1)
    if event == "ADDON_LOADED" then
        if arg1 == "BarPlan" then
            BarPlanDB = BarPlanDB or {}
            if BarPlanDB.auto == nil then BarPlanDB.auto = true end
        end
    elseif event == "PLAYER_REGEN_ENABLED" then
        if autoAfterCombat then autoAfterCombat = false; queueAutoFill() end
    elseif BarPlanDB then
        queueAutoFill()
    end
end)

------------------------------------------------------------------------
-- Slash command
------------------------------------------------------------------------

SLASH_BARPLAN1 = "/barplan"
SlashCmdList.BARPLAN = function(msg)
    msg = trim(msg):lower()
    if msg == "apply" then
        if BarPlanDB.last then BP.run(BarPlanDB.last, false)
        else say("No plan applied yet. Type /barplan and paste one.") end
    elseif msg == "auto" then
        BarPlanDB.auto = not BarPlanDB.auto
        say("Auto-fill new spells is " .. (BarPlanDB.auto and "on." or "off."))
        if frame then frame.auto:SetChecked(BarPlanDB.auto) end
    elseif msg == "export" then
        openFrame(BP.exportCurrent())
        frame.edit:SetFocus()
        frame.edit:HighlightText()
        frame.status:SetText("This is your current setup. Press Ctrl+C to copy it, then use Load in the planner.")
    elseif frame and frame:IsShown() then
        frame:Hide()
    else
        local fresh = not frame
        openFrame()
        if fresh and BarPlanDB.last then frame.edit:SetText(BarPlanDB.last) end
    end
end

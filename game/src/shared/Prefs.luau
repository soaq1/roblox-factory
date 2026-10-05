--!strict
-- What a player has set up for themselves and expects to find again: the ten slots of the hotbar
-- and the switches on the settings screen.
local Prefs = {}

Prefs.SLOTS = 10

-- Every setting and its starting value. A name not listed here is not a setting.
Prefs.DEFAULTS = {
	holdToRepeat = true, -- keep swinging while the button (or finger) stays down
	dragPlace = true, -- keep placing into new cells while the button stays down
	profilePublic = true, -- let other players see this player's card
} :: { [string]: boolean }

export type Saved = { bar: { string }, settings: { [string]: boolean } }

-- One hotbar: exactly SLOTS entries, each a known entry or "" for an empty slot.
function Prefs.cleanBar(raw: any, isEntry: (any) -> boolean): { string }
	local bar = table.create(Prefs.SLOTS, "")
	if type(raw) == "table" then
		for i = 1, Prefs.SLOTS do
			local entry = raw[i]
			if type(entry) == "string" and #entry <= 64 and isEntry(entry) then
				bar[i] = entry
			end
		end
	end
	return bar
end

-- Stored preferences made safe to use. A bar that was never saved comes back empty of entries.
function Prefs.sanitize(raw: any, isEntry: (any) -> boolean): Saved
	local saved: Saved = { bar = {}, settings = {} }
	if type(raw) ~= "table" then
		return saved
	end
	if type(raw.bar) == "table" and #raw.bar > 0 then
		saved.bar = Prefs.cleanBar(raw.bar, isEntry)
	end
	if type(raw.settings) == "table" then
		for name in Prefs.DEFAULTS do
			if type(raw.settings[name]) == "boolean" then
				saved.settings[name] = raw.settings[name]
			end
		end
	end
	return saved
end

-- The value of a setting: what was saved, or its starting value.
function Prefs.value(settings: { [string]: boolean }, name: string): boolean
	local saved = settings[name]
	if saved ~= nil then
		return saved
	end
	return Prefs.DEFAULTS[name] == true
end

return Prefs

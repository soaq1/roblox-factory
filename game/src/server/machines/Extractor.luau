-- Puts out one raw item at a steady pace: ore from a vein core, water from a pump.
--
-- With a belt or a machine at its mouth it sends what it makes there. With nothing at its mouth it
-- does not spill onto the ground: it keeps what it makes inside, stops when it is full, and F
-- gives what it holds to the owner. This is how the totems of the original game behaved.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local StatusText = require(Shared.StatusText)
local Kit = require(script.Parent.Parent.MachineKit)
local Outlet = require(script.Parent.Parent.Outlet)
local Profile = require(script.Parent.Parent.Profile)
local StatusKit = require(script.Parent.Parent.StatusKit)
local Tuning = require(script.Parent.Parent.Tuning)

local Extractor = {}

Extractor.STORE = 16 -- how many it holds when there is nowhere to send them (a placeholder)

local function refresh(machine)
	local code = "working"
	if machine.halted then
		code = "halted"
	elseif machine.stored >= Extractor.STORE then
		-- Full: either nothing is at the mouth to take it, or what is there is not taking it.
		code = if machine.out and Outlet.hasTaker(machine, machine.out) then "blocked" else "full"
	end
	StatusKit.set(machine, code)
	local lines = {}
	if machine.stored > 0 then
		table.insert(lines, Defs.name(machine.def.item) .. " " .. machine.stored .. " / " .. Extractor.STORE)
	end
	local rate = StatusKit.rate(machine)
	if rate > 0 then
		table.insert(lines, StatusText.rate(rate))
	end
	table.insert(lines, StatusText.of(code) .. (if code == "full" then " · F로 꺼내기" else ""))
	StatusKit.say(machine, table.concat(lines, "\n"))
end

function Extractor.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.out = Kit.outputs(Kit.ports(machine))[1]
	machine.timer = 0
	machine.stored = 0
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
	StatusKit.attach(machine)
	Kit.prompt(machine, body, "꺼내기", function(player)
		if player ~= machine.island.owner then
			return
		end
		if machine.stored < 1 then
			Profile.hint(player, "꺼낼 것이 없습니다")
			return
		end
		local n = machine.stored
		if Inventory.add(machine.island.bag, machine.def.item, n) then
			machine.stored = 0
			StatusKit.count(machine, n)
			Profile.push(machine.island)
			refresh(machine)
		end
	end)
	refresh(machine)
end

function Extractor.load(machine, saved)
	if type(saved) == "table" and type(saved.stored) == "number" and saved.stored == saved.stored then
		machine.stored = math.clamp(math.floor(saved.stored), 0, Extractor.STORE)
		refresh(machine)
	end
end

function Extractor.save(machine)
	return { stored = machine.stored }
end

function Extractor.tick(machine, dt: number)
	local out = machine.out
	if not out then
		return
	end
	-- Whatever is made goes into the store first; it stops when the store is full.
	machine.timer = math.min(machine.timer + dt * Tuning.speed, Config.EXTRACT_INTERVAL)
	if machine.timer >= Config.EXTRACT_INTERVAL and machine.stored < Extractor.STORE then
		machine.timer = 0
		machine.stored += 1
	end
	-- With a belt or a machine at the mouth, the store empties onto it, one item at a time.
	if machine.stored > 0 and Outlet.hasTaker(machine, out) then
		if Outlet.emit(machine, out, machine.def.item) then
			machine.stored -= 1
			StatusKit.count(machine, 1)
		end
	end
	refresh(machine)
end

-- A machine stopped by a signal gets no tick; the power system calls this to keep it saying so.
Extractor.whileHalted = refresh

-- What falls out when the extractor is broken.
function Extractor.drops(machine): { [string]: number }
	return if machine.stored > 0 then { [machine.def.item] = machine.stored } else {}
end

return Extractor

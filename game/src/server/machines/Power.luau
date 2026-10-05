-- Everything that makes, stores or carries electricity: the coal generator, the incinerator, the
-- wind turbine, the solar panel, the battery, the pole, and the endless reactor.
--
-- Each machine here only looks after itself: it says what it can give (`supply`) or hold
-- (`charge`), and burns its fuel. Who is joined to whom and who gets power is worked out by
-- PowerService, which writes back `throttle` (the share of a generator's output in use),
-- `charge`, and `net` (the figures for the network the machine is on).
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local PowerLogic = require(Shared.PowerLogic)
local Recipes = require(Shared.Recipes)
local ItemService = require(script.Parent.Parent.ItemService)
local Kit = require(script.Parent.Parent.MachineKit)

local Power = {}

-- All placeholder numbers.
Power.GENERATOR_WATTS = 100
Power.GENERATOR_SECONDS_PER_FUEL = 10 -- one unit of fuel value (a log is 1, coal 4) runs it this long flat out
Power.GENERATOR_STOCK = 32 -- fuel items it holds
Power.INCINERATOR_WATTS = 15
Power.INCINERATOR_SECONDS_PER_ITEM = 1
Power.INCINERATOR_MAX_SECONDS = 120 -- it keeps destroying beyond this, but banks no more burning time
Power.WIND_WATTS = 40 -- at full wind
Power.SOLAR_WATTS = 15 -- at noon under a clear sky
Power.BATTERY_CAPACITY = 6000 -- joules: a minute of one generator
Power.BATTERY_RATE = 100 -- watts in or out
Power.REACTOR_WATTS = 1e9

local function watts(n: number): string
	return tostring(math.floor(n + 0.5)) .. "W"
end

-- The figures for the network a machine is on, as one line.
local function netLine(machine): string
	local net = machine.net
	if not net then
		return "이어진 곳 없음"
	elseif net.endless then
		return "무한 전력"
	end
	local line = "공급 " .. watts(net.supply) .. " · 수요 " .. watts(net.demand)
	if net.capacity > 0 then
		line ..= " · 축전 " .. math.floor(net.stored / net.capacity * 100 + 0.5) .. "%"
	end
	return line
end

local function stockCount(machine): number
	local total = 0
	for _, n in machine.stock do
		total += n
	end
	return total
end

-- Takes whatever `wanted` allows from the machine's input mouths.
local function intake(machine, wanted: (string, number) -> number)
	for _, port in machine.ins do
		for _, part in ItemService.inBox(port.box, port.size) do
			local id, count = ItemService.info(part)
			if id then
				local n = wanted(id, count)
				if n > 0 then
					machine.take(id, ItemService.take(part, n))
				end
			end
		end
	end
end

local KINDS = {}

-- The coal generator: steady power for as long as it is fed, burning only as much as is used.
KINDS.generator = {
	build = function(machine)
		machine.stock = {}
		machine.burn = 0 -- seconds of burning left in the fire
		machine.take = function(id: string, n: number)
			if n > 0 then
				Inventory.add(machine.stock, id, n)
			end
		end
	end,
	room = function(machine, id: string, count: number): number
		if not Recipes.fuel[id] then
			return 0
		end
		return math.clamp(Power.GENERATOR_STOCK - stockCount(machine), 0, count)
	end,
	tick = function(machine, dt: number)
		local throttle = machine.throttle or 0
		if machine.burn <= 0 and throttle > 0 then
			-- Light the weakest fuel first, as the smelter does.
			local best: string? = nil
			for id in machine.stock do
				if not best or Recipes.fuel[id] < Recipes.fuel[best] then
					best = id
				end
			end
			if best and Inventory.remove(machine.stock, best, 1) then
				machine.burn += Recipes.fuel[best] * Power.GENERATOR_SECONDS_PER_FUEL
			end
		end
		machine.burn = math.max(0, machine.burn - dt * throttle)
		machine.supply = if machine.burn > 0 or next(machine.stock) then Power.GENERATOR_WATTS else 0
	end,
	text = function(machine): string
		local parts = {}
		for id, n in machine.stock do
			table.insert(parts, Defs.name(id) .. " " .. n)
		end
		table.sort(parts)
		local fuel = if #parts > 0 then table.concat(parts, " · ") else "연료 없음"
		return fuel .. " · 불 " .. math.ceil(machine.burn) .. "초\n" .. netLine(machine)
	end,
	save = function(machine)
		return { stock = table.clone(machine.stock), burn = math.floor(machine.burn) }
	end,
	load = function(machine, saved)
		machine.stock = Inventory.sanitize(saved.stock, function(id)
			return Recipes.fuel[id] ~= nil
		end)
		if type(saved.burn) == "number" and saved.burn == saved.burn then
			machine.burn = math.clamp(saved.burn, 0, 24 * Power.GENERATOR_SECONDS_PER_FUEL)
		end
	end,
	drops = function(machine)
		return table.clone(machine.stock)
	end,
}

-- The incinerator: destroys whatever it is given, always, and gives a little power while it burns.
KINDS.incinerator = {
	build = function(machine)
		machine.burn = 0
		machine.free = true -- it burns whether or not anyone wants the power, so that power is used first
		machine.take = function(id: string, n: number)
			local each = Power.INCINERATOR_SECONDS_PER_ITEM * (1 + (Recipes.fuel[id] or 0))
			machine.burn = math.min(Power.INCINERATOR_MAX_SECONDS, machine.burn + n * each)
		end
	end,
	room = function(_machine, _id: string, count: number): number
		return count
	end,
	tick = function(machine, dt: number)
		machine.burn = math.max(0, machine.burn - dt)
		machine.supply = if machine.burn > 0 then Power.INCINERATOR_WATTS else 0
	end,
	text = function(machine): string
		local fire = if machine.burn > 0
			then "태우는 중 " .. math.ceil(machine.burn) .. "초"
			else "넣는 것은 모두 사라짐"
		return fire .. "\n" .. netLine(machine)
	end,
	save = function(machine)
		return { burn = math.floor(machine.burn) }
	end,
	load = function(machine, saved)
		if type(saved.burn) == "number" and saved.burn == saved.burn then
			machine.burn = math.clamp(saved.burn, 0, Power.INCINERATOR_MAX_SECONDS)
		end
	end,
}

KINDS.wind = {
	build = function(machine)
		machine.free = true
	end,
	tick = function(machine)
		machine.supply = Power.WIND_WATTS * PowerLogic.wind(os.clock(), machine.island.slot)
	end,
	text = function(machine): string
		return "바람 " .. watts(machine.supply or 0) .. "\n" .. netLine(machine)
	end,
}

KINDS.solar = {
	build = function(machine)
		machine.free = true
	end,
	tick = function(machine)
		machine.supply = Power.SOLAR_WATTS * PowerLogic.solar(Lighting.ClockTime, os.clock())
	end,
	text = function(machine): string
		return "햇빛 " .. watts(machine.supply or 0) .. "\n" .. netLine(machine)
	end,
}

KINDS.battery = {
	build = function(machine)
		machine.charge = 0
		machine.capacity = Power.BATTERY_CAPACITY
		machine.rate = Power.BATTERY_RATE
	end,
	text = function(machine): string
		return "축전 "
			.. math.floor(machine.charge / machine.capacity * 100 + 0.5)
			.. "%\n"
			.. netLine(machine)
	end,
	save = function(machine)
		return { charge = math.floor(machine.charge) }
	end,
	load = function(machine, saved)
		if type(saved.charge) == "number" and saved.charge == saved.charge then
			machine.charge = math.clamp(saved.charge, 0, machine.capacity)
		end
	end,
}

KINDS.pole = {
	text = netLine,
}

-- The endless reactor: the whole island, with no poles and no limit.
KINDS.reactor = {
	build = function(machine)
		machine.supply = Power.REACTOR_WATTS
		machine.everywhere = true
		machine.free = true
	end,
	text = function(): string
		return "무한 전력\n섬의 모든 기계에 전기가 들어옴"
	end,
}

function Power.build(machine)
	local kind = KINDS[machine.def.power] or KINDS.pole
	machine.kind = kind
	Kit.visual(machine.model, machine.base, machine.id)
	-- A pole is a thin post: nothing should bump into a full cell of air around it.
	machine.body = Kit.body(machine, if machine.def.power == "pole" then 0.9 else nil)
	machine.ins = Kit.inputs(Kit.ports(machine))
	machine.supply = 0
	if kind.build then
		kind.build(machine)
	end
	machine.label = Kit.label(machine.body, machine.def.height)
	machine.shown = ""
end

function Power.load(machine, saved)
	if type(saved) == "table" and machine.kind.load then
		machine.kind.load(machine, saved)
	end
end

function Power.save(machine)
	return if machine.kind.save then machine.kind.save(machine) else nil
end

function Power.tick(machine, dt: number)
	local kind = machine.kind
	if kind.room then
		intake(machine, function(id, count)
			return kind.room(machine, id, count)
		end)
	end
	if kind.tick then
		kind.tick(machine, dt)
	end
	local text = kind.text(machine)
	if text ~= machine.shown then
		machine.shown = text
		machine.label.Text = text
	end
end

-- Called when a neighbouring machine hands an item straight over.
function Power.accept(machine, id: string, n: number): number
	local kind = machine.kind
	if not kind.room then
		return 0
	end
	local taken = kind.room(machine, id, n)
	if taken > 0 then
		machine.take(id, taken)
	end
	return taken
end

function Power.drops(machine): { [string]: number }
	return if machine.kind.drops then machine.kind.drops(machine) else {}
end

return Power

-- Any machine that turns things into other things: smelter, crusher, press, kiln and the rest.
-- What it accepts and makes comes from the recipe table, so adding a recipe needs no code.
--
-- Inside, the machine has slots: ingredients (and fuel, where it burns any) and finished products.
-- A belt fills and empties them through the mouths. A player can do the same by hand: F opens the
-- machine's window, where things go in from the bag and come back out to it.
--
-- Electricity: a machine whose definition says it needs power only works while it has it. Any
-- other machine works without, and if it happens to stand on a powered network it works faster
-- and gets more out of its fuel.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local ProcessLogic = require(Shared.ProcessLogic)
local Recipes = require(Shared.Recipes)
local StatusText = require(Shared.StatusText)
local Kit = require(script.Parent.Parent.MachineKit)
local ItemService = require(script.Parent.Parent.ItemService)
local Outlet = require(script.Parent.Parent.Outlet)
local Profile = require(script.Parent.Parent.Profile)
local StatusKit = require(script.Parent.Parent.StatusKit)
local Watch = require(script.Parent.Parent.Watch)

local Processor = {}

Processor.SPEED_ON_POWER = 1.5 -- how much faster an ordinary machine works on electricity (a placeholder)
Processor.FUEL_ON_POWER = 0.5 -- the share of its usual fuel it then uses per job (a placeholder)

local function isBoosted(machine): boolean
	return machine.powered == true and not machine.def.needsPower
end

-- What the machine is doing, as a code from shared/StatusText.
local function statusOf(machine): string
	if machine.unset then
		return "unset" -- an assembler that has not been told what to make
	end
	return ProcessLogic.status(machine.state, machine.rules, {
		halted = machine.halted == true,
		needsPower = machine.def.needsPower == true,
		powered = machine.powered == true,
		stuck = machine.stuckFor >= StatusKit.STUCK_SECONDS,
	})
end

local function describe(machine): string
	local state = machine.state
	local lines = {}
	if machine.title then
		table.insert(lines, machine.title)
	end
	local parts = {}
	for id, n in state.buf do
		table.insert(parts, Defs.name(id) .. " " .. n)
	end
	table.sort(parts)
	if #parts > 0 then
		table.insert(lines, table.concat(parts, " · "))
	end
	local figures = {}
	if machine.rules.usesFuel then
		table.insert(figures, "연료 " .. state.fuel)
	end
	local rate = StatusKit.rate(machine)
	if rate > 0 then
		table.insert(figures, StatusText.rate(rate))
	end
	if #figures > 0 then
		table.insert(lines, table.concat(figures, " · "))
	end
	if not machine.unset then
		local status = StatusText.of(machine.status)
		table.insert(lines, if isBoosted(machine) then status .. " · 전기로 가속" else status)
	end
	return table.concat(lines, "\n")
end

-- Brings the lamp and the label up to date.
local function refresh(machine)
	StatusKit.set(machine, statusOf(machine))
	StatusKit.say(machine, describe(machine))
end

-- What the machine's window shows.
local function snapshot(machine): { [string]: any }
	local state = machine.state
	local info: { [string]: any } = {
		buf = table.clone(state.buf),
		out = table.clone(state.out),
		fuel = state.fuel,
		usesFuel = machine.rules.usesFuel,
		status = machine.status,
		rate = StatusKit.rate(machine),
		boosted = isBoosted(machine),
	}
	-- A machine built on this one (the assembler) adds what its own part of the window needs.
	if machine.info then
		for key, value in machine.info() do
			info[key] = value
		end
	end
	return info
end

function Processor.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	local ports = Kit.ports(machine)
	local recipes = Recipes.byMachine[machine.id] or {}
	machine.body = body
	machine.ins = Kit.inputs(ports)
	machine.outs = Kit.outputs(ports)
	machine.nextOut = 1
	machine.rules = {
		recipes = recipes,
		usesFuel = Recipes.usesFuel[machine.id] == true,
		fuel = Recipes.fuel,
		cap = Config.MACHINE_BUFFER,
		outCap = Config.MACHINE_OUT,
		-- room for recipes that need more of something than the usual buffer holds
		caps = ProcessLogic.caps(recipes, Config.MACHINE_BUFFER),
	}
	machine.state = ProcessLogic.new()
	machine.label = Kit.label(body, machine.def.height)
	StatusKit.roomy(machine.label)
	machine.shown = ""
	StatusKit.attach(machine)
	Kit.prompt(machine, body, "열기", function(player)
		Processor.open(machine, player)
	end)
	refresh(machine)
end

-- Opens the machine's window for its owner.
function Processor.open(machine, player: Player)
	if player ~= machine.island.owner then
		return
	end
	refresh(machine)
	Watch.open(machine, player, "machine", snapshot(machine))
end

-- Brings the lamp, the label and any open window up to date after something changed.
function Processor.changed(machine)
	refresh(machine)
	Watch.push(machine, function()
		return snapshot(machine)
	end, true)
end

-- Changes what the machine makes. Returns whatever was waiting inside that the new recipes have
-- no use for, taken out of the machine.
function Processor.setRecipes(machine, recipes): { [string]: number }
	local rules, state = machine.rules, machine.state
	rules.recipes = recipes
	rules.caps = ProcessLogic.caps(recipes, rules.cap)
	state.progress = 0
	local unwanted = {}
	for id, n in state.buf do
		local keep = (rules.usesFuel and rules.fuel[id] ~= nil)
		for _, recipe in recipes do
			keep = keep or recipe.ins[id] ~= nil
		end
		if not keep then
			unwanted[id] = n
		end
	end
	for id in unwanted do
		state.buf[id] = nil
	end
	return unwanted
end

function Processor.load(machine, saved)
	machine.state = ProcessLogic.sanitize(saved, machine.rules, Defs.isItem)
	refresh(machine)
end

function Processor.save(machine)
	local s = machine.state
	return { buf = table.clone(s.buf), out = table.clone(s.out), fuel = s.fuel }
end

function Processor.tick(machine, dt: number)
	local state, rules = machine.state, machine.rules
	local needsPower = machine.def.needsPower == true
	local powered = machine.powered == true
	local boosted = powered and not needsPower
	rules.fuelPerJob = if boosted then Processor.FUEL_ON_POWER else nil

	for _, port in machine.ins do
		for _, part in ItemService.inBox(port.box, port.size) do
			local id, count = ItemService.info(part)
			if id then
				local wanted = math.min(count, ProcessLogic.room(state, id, rules))
				if wanted > 0 then
					ProcessLogic.insert(state, id, ItemService.take(part, wanted), rules)
				end
			end
		end
	end

	-- The power system reads this: a machine with nothing to do draws nothing.
	machine.busy = ProcessLogic.hasWork(state, rules)
	if powered or not needsPower then
		ProcessLogic.step(state, if boosted then dt * Processor.SPEED_ON_POWER else dt, rules)
	end

	local ready = ProcessLogic.peekOutput(state)
	local left = false
	if ready and #machine.outs > 0 then
		if Outlet.emit(machine, machine.outs[machine.nextOut], ready) then
			ProcessLogic.removeOutput(state, ready)
			StatusKit.count(machine, 1)
			left = true
		end
		machine.nextOut = machine.nextOut % #machine.outs + 1
	end
	StatusKit.stuck(machine, ready ~= nil, left, dt)

	refresh(machine)
	Watch.push(machine, function()
		return snapshot(machine)
	end)
end

-- A machine stopped by a signal gets no tick, so the power system calls this now and then to
-- keep its lamp, label and window saying so.
function Processor.whileHalted(machine)
	refresh(machine)
	Watch.push(machine, function()
		return snapshot(machine)
	end)
end

-- What the owner does in the machine's window:
--   "put"   { id, n }     from the bag into the ingredient slots, as many as fit
--   "take"  { slot, id }  everything of one kind from a slot ("buf" or "out") into the bag
--   "close"               the window was closed
function Processor.act(machine, player: Player, action: string, arg: any)
	if player ~= machine.island.owner then
		return
	end
	if action == "close" then
		Watch.close(machine, player)
		return
	end
	-- Whoever is using the window is watching it, even if they wandered off and came back.
	machine.watchers = machine.watchers or {}
	machine.watchers[player] = true
	if type(arg) ~= "table" then
		return
	end
	local island = machine.island
	local moved = 0
	if action == "put" then
		moved = ProcessLogic.deposit(machine.state, island.bag, arg.id, arg.n, machine.rules)
	elseif action == "take" then
		moved = ProcessLogic.withdraw(machine.state, island.bag, arg.slot, arg.id)
		if moved > 0 and arg.slot == "out" then
			-- taken by hand, but it is still something the machine made and gave up
			StatusKit.count(machine, moved)
		end
	else
		return
	end
	if moved > 0 then
		Profile.push(island)
	elseif action == "put" then
		Profile.hint(player, "이 기계가 받지 않거나 더 들어갈 자리가 없습니다")
	end
	Processor.changed(machine)
end

-- Called when a neighbouring machine hands an item straight over.
function Processor.accept(machine, id: string, n: number): number
	return ProcessLogic.insert(machine.state, id, n, machine.rules)
end

-- What falls out when the machine is broken.
function Processor.drops(machine): { [string]: number }
	local all = table.clone(machine.state.buf)
	for id, n in machine.state.out do
		all[id] = (all[id] or 0) + n
	end
	return all
end

return Processor

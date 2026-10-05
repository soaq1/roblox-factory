-- Tests the game can run on itself inside Studio, started from outside by the test plugin
-- (tools/FactorySelfTest.lua). The plugin sets Workspace's "SelfTest" attribute to the test's
-- arguments; this module runs the named scenario, prints what it sees as lines starting
-- "SELFTEST", and sets "SelfTestResult" when done, which ends the play test.
-- Nothing here runs outside Studio, or in Studio when the attribute is never set.
local HttpService = game:GetService("HttpService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TextChatService = game:GetService("TextChatService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Grid = require(Shared.Grid)
local HandArm = require(script.Parent.HandArm)
local IslandService = require(script.Parent.IslandService)
local ItemService = require(script.Parent.ItemService)
local MachineService = require(script.Parent.MachineService)
local Profile = require(script.Parent.Profile)
local Tuning = require(script.Parent.Tuning)

local SelfTest = {}

local function say(...)
	print("SELFTEST", ...)
end

-- A floor of stone away from the starter island, so a test factory has clear ground.
local function floor(island, x0: number, x1: number, z0: number, z1: number)
	for x = x0, x1 do
		for z = z0, z1 do
			IslandService.setBlock(island, x, 0, z, "stone")
		end
	end
end

local function put(island, problems: { string }, id: string, x: number, z: number, dir: number)
	local machine = MachineService.create(island, id, x, 1, z, dir, nil)
	if not machine then
		table.insert(problems, "could not place " .. id .. " at " .. x .. "," .. z)
	end
	return machine
end

-- Where every loose item on the island is, as "id@x,y,z" in cells.
local function looseItems(island): { string }
	local list = {}
	local folder = Workspace:FindFirstChild("Items")
	local parts: { Instance } = if folder then folder:GetChildren() else {}
	for _, part in parts do
		local id, count = ItemService.info(part)
		if id and part:IsA("BasePart") and IslandService.owns(island, part.Position) then
			local p = part.Position - island.origin
			table.insert(list, string.format("%s x%d @%.1f,%.1f,%.1f", id, count, p.X / 3, p.Y / 3, p.Z / 3))
		end
	end
	table.sort(list)
	return list
end

local function bagText(bag: { [string]: number }?): string
	local parts = {}
	if bag then
		for id, n in bag do
			table.insert(parts, id .. "=" .. n)
		end
	end
	table.sort(parts)
	return table.concat(parts, " ")
end

local scenarios = {}

-- Iron ore and coal out of extractors, along belts, through a smelter, into a storage unit.
-- Passes if ingots reach the storage unit.
function scenarios.iron_line(_player, island, args)
	local problems: { string } = {}
	island.mode = "creative"
	Tuning.speed = tonumber(args.speed) or 4
	floor(island, 14, 26, -3, 3)
	-- west to east along z = 0: extractor, belt, open belt (coal joins here), belt, smelter, belt, storage
	put(island, problems, "extractor_fe", 15, 0, 0)
	put(island, problems, "belt", 16, 0, 0)
	put(island, problems, "belt_open", 17, 0, 0)
	put(island, problems, "belt", 18, 0, 0)
	local smelter = put(island, problems, "smelter", 19, 0, 0)
	put(island, problems, "belt", 20, 0, 0)
	local storage = put(island, problems, "storage", 21, 0, 0)
	-- coal comes down from the north onto the open belt
	put(island, problems, "extractor_coal", 17, -2, 1)
	put(island, problems, "belt", 17, -1, 1)

	local seconds = tonumber(args.seconds) or 40
	for t = 2, seconds, 2 do
		task.wait(2)
		local s = smelter and smelter.state
		say(
			string.format("t=%d", t),
			"smelter",
			s and ("buf[" .. bagText(s.buf) .. "] out[" .. bagText(s.out) .. "] fuel=" .. tostring(s.fuel))
				or "none",
			"| storage[" .. bagText(storage and storage.state) .. "]",
			"| loose " .. table.concat(looseItems(island), "; ")
		)
	end
	local ingots = storage and storage.state and storage.state.ingot_fe or 0
	return { pass = ingots > 0 and #problems == 0, ingots = ingots, problems = problems }
end

-- Places every machine once and takes it away again. Passes if none fails to build.
function scenarios.all_machines(_player, island, _args)
	local problems: { string } = {}
	island.mode = "creative"
	local ids = {}
	for id, def in Defs.Machines do
		if not def.hidden then
			table.insert(ids, id)
		end
	end
	table.sort(ids)
	floor(island, 30, 30 + 12 * 5, -30, 30)
	local placed = 0
	for i, id in ids do
		local x = 30 + ((i - 1) % 12) * 5
		local z = -28 + math.floor((i - 1) / 12) * 6
		local below = island.cells[Grid.key(x, 0, z)]
		local needs = Defs.Machines[id].needsBelow
		if needs then
			IslandService.clearCell(island, Grid.key(x, 0, z))
			IslandService.setBlock(island, x, 0, z, needs[1])
		elseif not below then
			IslandService.setBlock(island, x, 0, z, "stone")
		end
		local machine = MachineService.create(island, id, x, 1, z, 0, nil)
		if machine then
			placed += 1
		else
			table.insert(problems, "could not place " .. id)
		end
	end
	task.wait(5) -- let every machine tick a few times: a tick that errors warns in the output
	local saved = 0
	for _, machine in MachineService.onIsland(island) do
		local ok, err = pcall(MachineService.saveState, machine)
		if ok then
			saved += 1
		else
			table.insert(problems, "save of " .. machine.id .. " failed: " .. tostring(err))
		end
	end
	local removed = 0
	for _, machine in MachineService.onIsland(island) do
		if machine.x >= 30 then
			local ok, err = pcall(function()
				if machine.mod.drops then
					machine.mod.drops(machine)
				end
				MachineService.remove(machine, false)
			end)
			if ok then
				removed += 1
			else
				table.insert(problems, "removing " .. machine.id .. " failed: " .. tostring(err))
			end
		end
	end
	return {
		pass = #problems == 0,
		kinds = #ids,
		placed = placed,
		saved = saved,
		removed = removed,
		problems = problems,
	}
end

-- Does nothing but keep the play test open for a while, so what the client prints can be read.
function scenarios.idle(_player, _island, args)
	task.wait(tonumber(args.seconds) or 20)
	return { pass = true }
end

-- Checks the two things a chat command needs before anyone types one: the place has to be on the
-- current chat system (a place built by Rojo defaults to the old one, which Roblox has removed),
-- and the commands have to have been registered. Whether typing one then works is for a person to
-- try; nothing here can type into the chat bar.
function scenarios.chat(_player, _island, _args)
	local problems: { string } = {}
	local version = TextChatService.ChatVersion
	say("chat version", tostring(version))
	if version ~= Enum.ChatVersion.TextChatService then
		table.insert(problems, "the place is on " .. tostring(version) .. ", where no command can arrive")
	end
	local found: { string } = {}
	for _, child in TextChatService:GetChildren() do
		if child:IsA("TextChatCommand") then
			table.insert(found, child.PrimaryAlias)
		end
	end
	table.sort(found)
	say("commands", table.concat(found, " "))
	if not table.find(found, "/mode") then
		table.insert(problems, "/mode was never registered")
	end
	return { pass = #problems == 0, version = tostring(version), commands = found, problems = problems }
end

-- How far the right upper arm is turned away from the body, in degrees. Raised for a held tool it
-- reads about 80; hanging down it reads about 0. The arm is animated on the player's own machine,
-- so this is the pose as it reaches everyone else.
local function armAngle(player: Player): number?
	local character = player.Character
	local upper = character and character:FindFirstChild("RightUpperArm")
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not (upper and root and upper:IsA("BasePart") and root:IsA("BasePart")) then
		return nil
	end
	local x = select(1, root.CFrame:ToObjectSpace(upper.CFrame):ToOrientation())
	return math.deg(x)
end

-- Holding something has to raise the arm, and keep it raised. Passes if the empty Tool stays in the
-- character, Roblox really equips it (it welds the handle to the hand as RightGrip), the arm comes
-- up, and letting go brings it down again.
function scenarios.arm(player, _island, args)
	local problems: { string } = {}
	local rounds = tonumber(args.seconds) or 10
	HandArm.hold(player, "item:pick_wood")
	task.wait(1.5) -- the animation takes a moment to blend in
	local raised = 0
	for t = 1, rounds do
		local state = HandArm.state(player)
		local angle = armAngle(player)
		say(
			string.format("arm t=%d", t),
			"tool=" .. tostring(state.tool),
			"equipped=" .. tostring(state.equipped),
			"angle=" .. (if angle then string.format("%.0f", angle) else "?")
		)
		if not state.tool then
			table.insert(problems, "the tool was gone by second " .. t)
		elseif not state.equipped then
			table.insert(problems, "Roblox never equipped the tool (no RightGrip) by second " .. t)
		end
		if angle and angle > 40 then
			raised += 1
		end
		task.wait(1)
	end
	if raised < rounds - 1 then
		table.insert(problems, "the arm was only up for " .. raised .. " of " .. rounds .. " seconds")
	end

	HandArm.hold(player, "")
	task.wait(1.5)
	local after = HandArm.state(player)
	local down = armAngle(player)
	say(
		"arm let go",
		"tool=" .. tostring(after.tool),
		"angle=" .. (if down then string.format("%.0f", down) else "?")
	)
	if after.tool then
		table.insert(problems, "the tool stayed after letting go")
	end
	if down and down > 40 then
		table.insert(problems, string.format("the arm stayed up after letting go (%.0f degrees)", down))
	end
	return { pass = #problems == 0, raisedSeconds = raised, of = rounds, problems = problems }
end

function SelfTest.start()
	if not RunService:IsStudio() then
		return
	end
	task.spawn(function()
		local raw = nil
		for _ = 1, 80 do
			raw = Workspace:GetAttribute("SelfTest")
			if raw then
				break
			end
			task.wait(0.25)
		end
		if type(raw) ~= "string" then
			-- Normal when the game is just being played in Studio by hand. Said out loud anyway,
			-- because when a test *was* asked for, this silence is the only sign it went astray.
			say("no scenario was handed over in 20 seconds; nothing to run")
			return
		end
		local args = HttpService:JSONDecode(raw)
		local scenario = scenarios[args.scenario]
		local result
		if not scenario then
			result = { pass = false, problems = { "no such scenario: " .. tostring(args.scenario) } }
		else
			local player = Players:GetPlayers()[1] or Players.PlayerAdded:Wait()
			local island = nil
			for _ = 1, 200 do
				island = IslandService.get(player)
				if island and island.extra.ready then
					break
				end
				task.wait(0.1)
			end
			if not island then
				result = { pass = false, problems = { "the island never became ready" } }
			else
				say("start", args.scenario)
				local ok, value = pcall(scenario, player, island, args)
				result = if ok
					then value
					else { pass = false, problems = { "the scenario failed: " .. tostring(value) } }
				Profile.push(island)
			end
		end
		say("result", HttpService:JSONEncode(result))
		Workspace:SetAttribute("SelfTestResult", HttpService:JSONEncode(result))
	end)
end

return SelfTest

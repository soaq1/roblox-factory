-- Saving and loading islands. Uses Roblox's data store when it is available, and a store that only
-- lasts while the server runs when it is not (an unpublished place opened in Studio).
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Codec = require(Shared.Codec)
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Grid = require(Shared.Grid)
local IslandService = require(script.Parent.IslandService)
local MachineService = require(script.Parent.MachineService)

local SaveService = {}

local STORE_NAME = "island_v1"
-- In Studio a failure almost always means the data store is switched off, so do not wait and retry.
local ATTEMPTS = if RunService:IsStudio() then 1 else 3
local CHECKS: Codec.Checks =
	{ isBlock = Defs.isBlock, isMachine = Defs.isMachine, maxCoord = Config.MAX_COORD }

local memory: { [string]: any } = {}
local useMemory = false

local function setMode()
	Workspace:SetAttribute("SaveMode", if useMemory then "임시" else "저장소")
end

local function keyFor(player: Player): string
	return "u_" .. player.UserId
end

local function attempt<T>(fn: () -> T): (boolean, T | string)
	local lastError = "unknown"
	for try = 1, ATTEMPTS do
		local ok, result = pcall(fn)
		if ok then
			return true, result
		end
		lastError = tostring(result)
		if try < ATTEMPTS then
			task.wait(try)
		end
	end
	return false, lastError
end

export type LoadResult = {
	status: "new" | "loaded" | "unreadable" | "failed",
	island: Codec.Island?,
	skipped: number,
}

function SaveService.load(player: Player): LoadResult
	local key = keyFor(player)
	local raw: any
	if useMemory then
		raw = memory[key]
	else
		local ok, result = attempt(function()
			return DataStoreService:GetDataStore(STORE_NAME):GetAsync(key)
		end)
		if ok then
			raw = result
		elseif RunService:IsStudio() then
			-- Studio without data store access: keep going with memory so the game is still testable.
			warn("data store unavailable, using a temporary store: " .. tostring(result))
			useMemory = true
			setMode()
			raw = memory[key]
		else
			warn("could not load island for " .. player.Name .. ": " .. tostring(result))
			return { status = "failed", island = nil, skipped = 0 }
		end
	end
	if raw == nil then
		return { status = "new", island = nil, skipped = 0 }
	end
	local island, skipped = Codec.decode(raw, CHECKS)
	if not island then
		return { status = "unreadable", island = nil, skipped = 0 }
	end
	return { status = "loaded", island = island, skipped = skipped }
end

local function snapshot(island: IslandService.Island): { [string]: any }
	local data: Codec.Island = { blocks = {}, machines = {}, bag = table.clone(island.bag) }
	for key, cell in island.cells do
		local x, y, z = Grid.parseKey(key)
		if x and y and z then
			if cell.kind == "block" then
				table.insert(data.blocks, { x = x, y = y, z = z, id = cell.id })
			else
				table.insert(data.machines, {
					id = cell.id,
					x = x,
					y = y,
					z = z,
					d = cell.machine.dir,
					s = MachineService.saveState(cell.machine),
				})
			end
		end
	end
	return Codec.encode(data)
end

function SaveService.save(player: Player): boolean
	local island = IslandService.get(player)
	-- An island whose stored copy could not be read is never written back, so the original is kept.
	if not island or not island.canSave then
		return false
	end
	local key = keyFor(player)
	local data = snapshot(island)
	if useMemory then
		memory[key] = data
		return true
	end
	local ok, err = attempt(function()
		DataStoreService:GetDataStore(STORE_NAME):SetAsync(key, data)
		return true
	end)
	if not ok then
		warn("could not save island for " .. player.Name .. ": " .. tostring(err))
	end
	return ok
end

function SaveService.start()
	setMode()
	task.spawn(function()
		while true do
			task.wait(Config.AUTOSAVE_SECONDS)
			for player in IslandService.all() do
				task.spawn(SaveService.save, player)
			end
		end
	end)
	game:BindToClose(function()
		local pending = 0
		for player in IslandService.all() do
			pending += 1
			task.spawn(function()
				SaveService.save(player)
				pending -= 1
			end)
		end
		local deadline = os.clock() + 20
		while pending > 0 and os.clock() < deadline do
			task.wait(0.1)
		end
	end)
end

return SaveService

-- What a player owns apart from the island itself: the bag, coins, workbench tiers and play mode.
-- This module tells the client when any of it changes and reads it back from stored data.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local CraftLogic = require(Shared.CraftLogic)
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local Wallet = require(Shared.Wallet)
local Stock = require(Shared.Stock)(Defs)

local Profile = {}

Profile.Stock = Stock

function Profile.push(island)
	local player = island.owner
	Net.get("Bag"):FireClient(player, island.bag)
	Net.get("State"):FireClient(player, { mode = island.mode, coins = island.coins, tiers = island.tiers })
end

function Profile.notify(player: Player, text: string)
	Net.get("Notify"):FireClient(player, text)
end

-- Fills an island's owner data from what was stored, falling back to a fresh start for any part
-- that is missing or not valid.
function Profile.load(island, bag: any, stored: any)
	island.bag = Inventory.sanitize(bag, Stock.isKey)
	if type(stored) ~= "table" then
		return
	end
	island.coins = Wallet.sanitize(stored.coins, Config.START_COINS)
	island.tiers = CraftLogic.sanitizeTiers(stored.tiers)
	if stored.mode == "creative" or stored.mode == "survival" then
		island.mode = stored.mode
	end
	if type(stored.fuel) == "number" and stored.fuel == stored.fuel then
		island.handFuel = math.clamp(math.floor(stored.fuel), 0, 64)
	end
end

function Profile.save(island): { [string]: any }
	return {
		mode = island.mode,
		coins = island.coins,
		tiers = table.clone(island.tiers),
		fuel = island.handFuel,
	}
end

return Profile

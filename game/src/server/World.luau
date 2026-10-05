-- Where the shared places are, and what the systems that build them tell each other.
-- Islands sit along +X starting at one ISLAND_SPACING from the origin, so everything here is
-- placed well away from that line.
local World = {}

World.HUB_ORIGIN = Vector3.new(0, 0, 0) -- the centre of the hub's floor, at the height of an island's ground top
World.MONSTER_ORIGIN = Vector3.new(0, 0, 3000)

-- The merchants standing in the hub.
World.MERCHANTS = { "farmer", "miner", "cook", "builder" }
World.MERCHANT_NAMES = { farmer = "농부", miner = "광부", cook = "요리사", builder = "건축가" }
World.MERCHANT_RANGE = 14 -- studs from a merchant within which their counter can be used

-- Filled in by whoever builds the hub: where each merchant stands.
World.merchantAt = {} :: { [string]: Vector3 }

return World

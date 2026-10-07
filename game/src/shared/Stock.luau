--!nocheck
-- What a bag can hold in the real (non-creative) game, and how the things placed in the world turn
-- into bag entries and back. A bag key is an item id, a machine id, or "block:<id>" for a block.
-- Takes the definitions as an argument so it can be tested outside Roblox:
--     local Stock = require(Shared.Stock)(Defs)
return function(Defs)
	local Stock = {}

	local BLOCK = "block:"
	-- Blocks that come apart into something else when broken, and are placed from that same thing.
	local BREAKS_INTO = { dirt = "dirt_clod" }
	-- Blocks that fall apart into something they cannot be put back from: dug-up farmland is just
	-- dirt again, and has to be tilled with a hoe to be farmland once more.
	local CRUMBLES_TO = { farmland = "dirt_clod" }

	Stock.SAPLING_CHANCE = 0.1 -- how often breaking leaves gives a sapling

	-- The block id inside a "block:<id>" key.
	function Stock.blockOf(key): string?
		if type(key) == "string" and string.sub(key, 1, #BLOCK) == BLOCK then
			local id = string.sub(key, #BLOCK + 1)
			return if Defs.Blocks[id] then id else nil
		end
		return nil
	end

	function Stock.isKey(key): boolean
		return Defs.isItem(key) or Defs.isMachine(key) or Stock.blockOf(key) ~= nil
	end

	function Stock.name(key): string
		local block = Stock.blockOf(key)
		if block then
			return Defs.Blocks[block].name .. " 블록"
		end
		return Defs.name(key)
	end

	local LOOSE_BLOCK = { 1.5, 1.5, 1.5 } -- studs: a block lying loose is half a cell across

	-- What a bag key looks like lying loose in the world: its size, colour and whether it is round.
	-- An item is as its definition says. A block that is only a block is a small box in its top
	-- colour. A machine cannot lie loose, and nor can anything that is not a bag key.
	function Stock.loose(key): { size: { number }, color: { number }, ball: boolean }?
		local item = Defs.Items[key]
		if item then
			return { size = item.size, color = item.color, ball = item.ball }
		end
		local block = Stock.blockOf(key)
		if block then
			return { size = LOOSE_BLOCK, color = Defs.Blocks[block].top, ball = false }
		end
		return nil
	end

	-- What goes into the bag when a block is broken. `roll` is a random number from 0 up to 1.
	function Stock.blockDrop(id: string, roll: number): string?
		if id == "leaves" then
			return if roll < Stock.SAPLING_CHANCE then "sapling" else nil
		end
		if BREAKS_INTO[id] or CRUMBLES_TO[id] then
			return BREAKS_INTO[id] or CRUMBLES_TO[id]
		end
		-- A block that is also an item (log, stone, ore) comes back as the item.
		if Defs.Items[id] then
			return id
		end
		return BLOCK .. id
	end

	-- The bag keys that can pay for placing something, in the order they are tried.
	function Stock.placeCost(entry: string): { string }
		if Defs.Blocks[entry] then
			local keys = { BLOCK .. entry }
			if Defs.Items[entry] then
				table.insert(keys, entry)
			end
			if BREAKS_INTO[entry] then
				table.insert(keys, BREAKS_INTO[entry])
			end
			return keys
		end
		local machine = Defs.Machines[entry]
		if machine then
			return { machine.cost or entry }
		end
		return {}
	end

	-- What goes into the bag when a machine is broken. Plants give nothing here: what they yield
	-- depends on how far they have grown, and they drop that themselves.
	function Stock.machineReturn(id: string): string?
		local machine = Defs.Machines[id]
		if not machine or machine.cost then
			return nil
		end
		return id
	end

	return Stock
end

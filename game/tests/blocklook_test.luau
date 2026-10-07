-- How blocks are drawn:  lune run tests/blocklook_test.luau
local T = require("./harness")
local BlockLook = require("../src/shared/BlockLook")
local Defs = require("../src/shared/Defs")

local test, eq = T.test, T.eq

test("grass, dirt and stone wear their uploaded pictures", function()
	for _, id in { "grass", "dirt", "stone" } do
		local look = BlockLook.of(id, Defs.Blocks[id])
		eq(look.variant, "Block_" .. id)
		assert(look.side and string.match(look.side, "^rbxassetid://%d+$"), id .. " has no side picture")
		eq(look.cap, nil)
	end
	assert(BlockLook.of("grass", Defs.Blocks.grass).top ~= nil, "grass has a top of its own")
	eq(BlockLook.of("dirt", Defs.Blocks.dirt).top, nil)
	eq(BlockLook.of("stone", Defs.Blocks.stone).top, nil)
end)

test("a block with no picture is drawn plain, with a cap only when its top differs", function()
	local plain = { name = "x", color = { 100, 100, 100 }, top = { 100, 100, 100 }, transparency = 0 }
	local look = BlockLook.of("x", plain)
	eq(look.variant, nil)
	eq(look.side, nil)
	eq(look.top, nil)
	eq(look.cap, nil)
	local capped = { name = "y", color = { 100, 100, 100 }, top = { 200, 100, 100 }, transparency = 0 }
	eq(BlockLook.of("y", capped).cap[1], 200)
	-- the blocks that had a cap before still have one, until their pictures are uploaded
	for _, id in { "log", "farmland" } do
		local def = Defs.Blocks[id]
		if not def.tex then
			assert(BlockLook.of(id, def).cap ~= nil, id .. " lost its cap")
		end
	end
end)

test("a textured block needs no cap, even when its plain colours would have called for one", function()
	local def = { color = { 0, 0, 0 }, top = { 255, 255, 255 }, tex = { side = "rbxassetid://1" } }
	local look = BlockLook.of("z", def)
	eq(look.cap, nil)
	eq(look.variant, "Block_z")
end)

test("every picture is a Roblox picture number, and only 'side' and 'top' are named", function()
	for id, def in Defs.Blocks do
		if def.tex then
			for face, image in def.tex do
				assert(face == "side" or face == "top", id .. " names an unknown face " .. tostring(face))
				assert(
					string.match(image, "^rbxassetid://%d+$"),
					id .. "." .. face .. " is not a picture number"
				)
			end
			assert(def.tex.side, id .. " has a top picture but no side picture")
		end
	end
end)

test("one custom material per textured block, in a fixed order", function()
	local list = BlockLook.variants(Defs.Blocks)
	local names = {}
	for _, v in list do
		table.insert(names, v.name)
	end
	eq(table.concat(names, ","), "Block_dirt,Block_grass,Block_stone")
	eq(#BlockLook.variants({}), 0)
end)

T.done()

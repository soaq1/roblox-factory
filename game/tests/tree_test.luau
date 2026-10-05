-- Runs outside Roblox:  lune run tests/tree_test.luau
local T = require("./harness")
local TreeGen = require("../src/shared/TreeGen")
local test, eq = T.test, T.eq

test("the same seed always gives the same tree", function()
	local a, b = TreeGen.make(12345), TreeGen.make(12345)
	eq(a.height, b.height)
	eq(a.logs, b.logs)
	eq(#a.limbs, #b.limbs)
	eq(#a.lumps, #b.lumps)
	eq(#a.cells, #b.cells)
	for i, limb in a.limbs do
		eq(limb.bx, b.limbs[i].bx)
		eq(limb.r, b.limbs[i].r)
	end
	for i, cell in a.cells do
		eq(cell[1], b.cells[i][1])
		eq(cell[2], b.cells[i][2])
		eq(cell[3], b.cells[i][3])
	end
end)
test("different seeds give different trees", function()
	local seen = {}
	for seed = 1, 40 do
		seen[TreeGen.make(seed).height] = true
	end
	local count = 0
	for _ in seen do
		count += 1
	end
	assert(count > 30, "too many trees came out the same: " .. count)
end)
test("small seeds are as varied as large ones", function()
	local lo, hi = math.huge, -math.huge
	for seed = 1, 30 do
		local h = TreeGen.make(seed).height
		lo, hi = math.min(lo, h), math.max(hi, h)
	end
	assert(hi - lo > 2, "seeds 1 to 30 all gave nearly the same height")
end)
test("ordinary trees differ only a little", function()
	for seed = 1, 300 do
		local tree = TreeGen.make(seed * 7919)
		assert(tree.height >= 15 and tree.height <= 18.5, "height out of range: " .. tree.height)
		assert(tree.logs >= 5 and tree.logs <= 7, "logs out of range: " .. tree.logs)
		assert(#tree.limbs >= 11 and #tree.limbs <= 13, "odd number of limbs: " .. #tree.limbs)
		assert(#tree.lumps == 16 or #tree.lumps == 20, "odd number of leaf lumps: " .. #tree.lumps)
		eq(tree.giant, false)
		eq(tree.hardness, 12)
	end
end)
test("the first cell kept is the one the trunk stands in, and none is listed twice", function()
	for seed = 1, 100 do
		local tree = TreeGen.make(seed * 31 + 5)
		eq(tree.cells[1][1], 0)
		eq(tree.cells[1][2], 0)
		eq(tree.cells[1][3], 0)
		local seen = {}
		for _, cell in tree.cells do
			local key = cell[1] .. "," .. cell[2] .. "," .. cell[3]
			assert(not seen[key], "cell listed twice: " .. key)
			seen[key] = true
			assert(cell[2] >= 0, "a tree keeps nothing below the ground")
		end
	end
end)
test("the ground around an ordinary trunk stays free to build on", function()
	for seed = 1, 200 do
		local tree = TreeGen.make(seed * 104729)
		local low = 0
		for _, cell in tree.cells do
			-- the two layers a player walks and builds in
			if cell[2] <= 1 then
				low += 1
				assert(math.abs(cell[1]) <= 1 and math.abs(cell[3]) <= 1, "low cell far from the trunk")
			end
		end
		assert(low <= 6, "too much kept at ground level: " .. low)
	end
end)
test("leaves keep cells well above head height, and not absurdly many", function()
	for seed = 1, 200 do
		local tree = TreeGen.make(seed * 613)
		local high = 0
		for _, cell in tree.cells do
			if cell[2] >= 3 then
				high += 1
			end
		end
		assert(high >= 8, "a tree with almost no crown: " .. high)
		assert(#tree.cells <= 140, "an ordinary tree keeps too many cells: " .. #tree.cells)
	end
end)
test("a giant is much bigger in every way", function()
	local small, giant = TreeGen.make(77), TreeGen.make(77, true)
	eq(giant.giant, true)
	assert(giant.height > small.height * 2, "giant is not tall")
	assert(#giant.cells > #small.cells * 4, "giant keeps too few cells")
	assert(giant.logs > small.logs * 5, "giant gives too few logs")
	assert(giant.hardness > small.hardness * 3, "giant is too easy to fell")
end)
test("giants are rare, and a felled tree always gives a sapling back", function()
	eq(TreeGen.isGiant(0), true)
	eq(TreeGen.isGiant(TreeGen.GIANT_CHANCE), false)
	eq(TreeGen.isGiant(0.5), false)
	eq(TreeGen.saplings(0.1), 2)
	eq(TreeGen.saplings(0.9), 1)
end)

T.done()

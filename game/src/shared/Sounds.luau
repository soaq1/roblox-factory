-- Every sound the game plays, by name. `id` is a Roblox audio asset number; 0 means "not chosen
-- yet", and the game simply stays quiet for that sound. Pick sounds in Studio's Toolbox (Audio),
-- listen to them there, and put the number here. `find` is what to search for.
-- `volume` is 0 to 1; `pitch` gives a little random variation so repeats do not sound identical.
return {
	-- the hand
	hit_wood = { id = 0, volume = 0.5, pitch = 0.15, find = "wood hit, axe chop" },
	hit_stone = { id = 0, volume = 0.5, pitch = 0.15, find = "stone hit, pickaxe" },
	hit_dirt = { id = 0, volume = 0.5, pitch = 0.15, find = "dirt dig, shovel" },
	hit_other = { id = 0, volume = 0.4, pitch = 0.15, find = "soft hit, thud" },
	place = { id = 0, volume = 0.5, pitch = 0.1, find = "block place, pop" },
	till = { id = 0, volume = 0.5, pitch = 0.1, find = "hoe till soil" },
	-- items
	pickup = { id = 0, volume = 0.4, pitch = 0.2, find = "item pickup pop" },
	drop = { id = 0, volume = 0.3, pitch = 0.2, find = "drop item, soft plop" },
	-- screens
	click = { id = 0, volume = 0.3, pitch = 0, find = "ui click" },
	open = { id = 0, volume = 0.3, pitch = 0, find = "ui open, inventory open" },
	craft = { id = 0, volume = 0.5, pitch = 0.05, find = "craft success, anvil ding" },
	coin = { id = 0, volume = 0.5, pitch = 0.05, find = "coin" },
	-- the world
	portal = { id = 0, volume = 0.6, pitch = 0, find = "portal whoosh, teleport" },
	slime = { id = 0, volume = 0.5, pitch = 0.2, find = "slime squish" },
}

-- A tiny test harness shared by the test files.
--     local T = require("./harness")
--     T.test("name", function() T.eq(1 + 1, 2) end)
--     T.done()
local T = {}

local passed, failed = 0, 0

function T.test(name: string, fn: () -> ())
	local ok, err = pcall(fn)
	if ok then
		passed += 1
	else
		failed += 1
		print("FAIL  " .. name .. "\n      " .. tostring(err))
	end
end

function T.eq(a: any, b: any, what: string?)
	if a ~= b then
		error((what or "values") .. ": expected " .. tostring(b) .. ", got " .. tostring(a), 2)
	end
end

-- Prints the totals and makes the run fail if anything did.
function T.done()
	print(string.format("%d passed, %d failed", passed, failed))
	if failed > 0 then
		(require("@lune/process") :: any).exit(1)
	end
end

return T

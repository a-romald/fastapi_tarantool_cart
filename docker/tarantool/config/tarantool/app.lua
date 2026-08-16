#!/usr/bin/env tarantool

-- Configure database
box.cfg {    
}

-- Initialize Data schema on first run
box.once("bootstrap", function()

    -- Temporal data space
    box.schema.create_space('shop', {
        id     = 100,
        engine = 'vinyl'
    })

    -- Specify field names and types --
    box.space.shop:format({
        { name = 'type', type = 'string' },
        { name = 'key', type = 'string' },
        { name = 'data', type = 'any' },
        { name = 'expires', type = 'unsigned' }
    })

    -- Index by type and key, e.g. str(key_type), str(key)
    box.space.shop:create_index('primary', {
        type  = 'TREE',
        parts = {1, 'string', 2, 'string'}
    })

    -- Index by type, e.g. cart, session
    box.space.shop:create_index('type', {
        type   = 'TREE',
        parts  = {1, 'string'},
        unique = false
    })

    -- Obsolescence and Expiration Index
    box.space.shop:create_index('expires', {
        type   = 'TREE',
        parts  = {4, 'unsigned'},
        unique = false
    })

end)

----------------------------------------------------------------

-- Function for checking the presence of a key
function exists(space, key)
  local s = box.space[space]
  return s:count(key, {iterator='EQ'})
end

----------------------------------------------------------------

-- Data invalidation (deleting records with expired lifespan)
expirationd = require('expirationd')

-- Check if the entry has expired
function is_expired(args, tuple)
  return tuple[4] < os.time()
end

-- Delete entry record
function delete_tuple(space_id, args, tuple)
  box.space[space_id]:delete{tuple[1],tuple[2]}
end

-- Run a cyclic check for record expiration
expirationd.start("drop_expired", box.space.shop.id, is_expired, {
    process_expired_tuple = delete_tuple,
    args = nil,
    tuples_per_iteration = 1000,
    full_scan_time = 3600,
    force = true
})

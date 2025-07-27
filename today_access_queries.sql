-- =====================================================
-- TODAY'S ACCESS QUERIES - FASTag System
-- =====================================================

-- 1. BASIC TODAY'S GRANTED AND DENIED COUNTS
-- =====================================================

-- Total granted today
SELECT 
    COUNT(*) as total_granted_today
FROM access_logs 
WHERE access_result = 'granted' 
    AND DATE(timestamp) = DATE('now');

-- Total denied today
SELECT 
    COUNT(*) as total_denied_today
FROM access_logs 
WHERE access_result = 'denied' 
    AND DATE(timestamp) = DATE('now');

-- Combined granted and denied today
SELECT 
    access_result,
    COUNT(*) as count_today
FROM access_logs 
WHERE DATE(timestamp) = DATE('now')
GROUP BY access_result
ORDER BY access_result;

-- 2. GRANTED AND DENIED BY READER TYPE (ENTRY/EXIT)
-- =====================================================

-- Granted by reader type today
SELECT 
    r.type as reader_type,
    COUNT(*) as granted_count
FROM access_logs al
JOIN readers r ON al.reader_id = r.id
WHERE al.access_result = 'granted' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY r.type
ORDER BY r.type;

-- Denied by reader type today
SELECT 
    r.type as reader_type,
    COUNT(*) as denied_count
FROM access_logs al
JOIN readers r ON al.reader_id = r.id
WHERE al.access_result = 'denied' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY r.type
ORDER BY r.type;

-- Combined by reader type today
SELECT 
    r.type as reader_type,
    al.access_result,
    COUNT(*) as count_today
FROM access_logs al
JOIN readers r ON al.reader_id = r.id
WHERE DATE(al.timestamp) = DATE('now')
GROUP BY r.type, al.access_result
ORDER BY r.type, al.access_result;

-- 3. GRANTED AND DENIED BY LANE
-- =====================================================

-- Granted by lane today
SELECT 
    l.lane_name,
    COUNT(*) as granted_count
FROM access_logs al
JOIN lanes l ON al.lane_id = l.id
WHERE al.access_result = 'granted' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY l.id, l.lane_name
ORDER BY l.lane_name;

-- Denied by lane today
SELECT 
    l.lane_name,
    COUNT(*) as denied_count
FROM access_logs al
JOIN lanes l ON al.lane_id = l.id
WHERE al.access_result = 'denied' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY l.id, l.lane_name
ORDER BY l.lane_name;

-- Combined by lane today
SELECT 
    l.lane_name,
    al.access_result,
    COUNT(*) as count_today
FROM access_logs al
JOIN lanes l ON al.lane_id = l.id
WHERE DATE(al.timestamp) = DATE('now')
GROUP BY l.id, l.lane_name, al.access_result
ORDER BY l.lane_name, al.access_result;

-- 4. GRANTED AND DENIED BY HOUR TODAY
-- =====================================================

-- Granted by hour today
SELECT 
    strftime('%H:00', al.timestamp) as hour,
    COUNT(*) as granted_count
FROM access_logs al
WHERE al.access_result = 'granted' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY strftime('%H', al.timestamp)
ORDER BY hour;

-- Denied by hour today
SELECT 
    strftime('%H:00', al.timestamp) as hour,
    COUNT(*) as denied_count
FROM access_logs al
WHERE al.access_result = 'denied' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY strftime('%H', al.timestamp)
ORDER BY hour;

-- Combined by hour today
SELECT 
    strftime('%H:00', al.timestamp) as hour,
    al.access_result,
    COUNT(*) as count_today
FROM access_logs al
WHERE DATE(al.timestamp) = DATE('now')
GROUP BY strftime('%H', al.timestamp), al.access_result
ORDER BY hour, al.access_result;

-- 5. GRANTED AND DENIED BY TAG TYPE (FASTag vs Non-FASTag)
-- =====================================================

-- Granted by tag type today (FASTag starts with 34161)
SELECT 
    CASE 
        WHEN al.tag_id LIKE '34161%' THEN 'FASTag'
        ELSE 'Non-FASTag'
    END as tag_type,
    COUNT(*) as granted_count
FROM access_logs al
WHERE al.access_result = 'granted' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY CASE 
    WHEN al.tag_id LIKE '34161%' THEN 'FASTag'
    ELSE 'Non-FASTag'
END
ORDER BY tag_type;

-- Denied by tag type today
SELECT 
    CASE 
        WHEN al.tag_id LIKE '34161%' THEN 'FASTag'
        ELSE 'Non-FASTag'
    END as tag_type,
    COUNT(*) as denied_count
FROM access_logs al
WHERE al.access_result = 'denied' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY CASE 
    WHEN al.tag_id LIKE '34161%' THEN 'FASTag'
    ELSE 'Non-FASTag'
END
ORDER BY tag_type;

-- 6. DETAILED GRANTED EVENTS TODAY WITH USER INFO
-- =====================================================

-- Granted events with user details today
SELECT 
    al.tag_id,
    al.timestamp,
    r.type as reader_type,
    l.lane_name,
    ku.name as user_name,
    ku.vehicle_number,
    ku.contact_number
FROM access_logs al
JOIN readers r ON al.reader_id = r.id
JOIN lanes l ON al.lane_id = l.id
LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
WHERE al.access_result = 'granted' 
    AND DATE(al.timestamp) = DATE('now')
ORDER BY al.timestamp DESC;

-- 7. DETAILED DENIED EVENTS TODAY
-- =====================================================

-- Denied events with reason today
SELECT 
    al.tag_id,
    al.timestamp,
    al.reason,
    r.type as reader_type,
    l.lane_name
FROM access_logs al
JOIN readers r ON al.reader_id = r.id
JOIN lanes l ON al.lane_id = l.id
WHERE al.access_result = 'denied' 
    AND DATE(al.timestamp) = DATE('now')
ORDER BY al.timestamp DESC;

-- 8. SUMMARY DASHBOARD QUERY
-- =====================================================

-- Complete summary for today
SELECT 
    'Total Events' as metric,
    COUNT(*) as value
FROM access_logs 
WHERE DATE(timestamp) = DATE('now')

UNION ALL

SELECT 
    'Granted Events',
    COUNT(*)
FROM access_logs 
WHERE access_result = 'granted' 
    AND DATE(timestamp) = DATE('now')

UNION ALL

SELECT 
    'Denied Events',
    COUNT(*)
FROM access_logs 
WHERE access_result = 'denied' 
    AND DATE(timestamp) = DATE('now')

UNION ALL

SELECT 
    'Unique Tags',
    COUNT(DISTINCT tag_id)
FROM access_logs 
WHERE DATE(timestamp) = DATE('now')

UNION ALL

SELECT 
    'FASTag Events',
    COUNT(*)
FROM access_logs 
WHERE tag_id LIKE '34161%' 
    AND DATE(timestamp) = DATE('now')

UNION ALL

SELECT 
    'Non-FASTag Events',
    COUNT(*)
FROM access_logs 
WHERE tag_id NOT LIKE '34161%' 
    AND DATE(timestamp) = DATE('now');

-- 9. HOURLY ACTIVITY SUMMARY TODAY
-- =====================================================

-- Hourly activity with granted/denied breakdown
SELECT 
    strftime('%H:00', al.timestamp) as hour,
    COUNT(CASE WHEN al.access_result = 'granted' THEN 1 END) as granted,
    COUNT(CASE WHEN al.access_result = 'denied' THEN 1 END) as denied,
    COUNT(*) as total
FROM access_logs al
WHERE DATE(al.timestamp) = DATE('now')
GROUP BY strftime('%H', al.timestamp)
ORDER BY hour;

-- 10. READER PERFORMANCE TODAY
-- =====================================================

-- Reader performance summary today
SELECT 
    r.id as reader_id,
    r.type as reader_type,
    l.lane_name,
    COUNT(CASE WHEN al.access_result = 'granted' THEN 1 END) as granted,
    COUNT(CASE WHEN al.access_result = 'denied' THEN 1 END) as denied,
    COUNT(*) as total_events
FROM access_logs al
JOIN readers r ON al.reader_id = r.id
JOIN lanes l ON al.lane_id = l.id
WHERE DATE(al.timestamp) = DATE('now')
GROUP BY r.id, r.type, l.lane_name
ORDER BY r.id;

-- 11. MOST ACTIVE TAGS TODAY
-- =====================================================

-- Most active tags today (granted)
SELECT 
    al.tag_id,
    COUNT(*) as granted_count,
    ku.name as user_name,
    ku.vehicle_number
FROM access_logs al
LEFT JOIN kyc_users ku ON al.tag_id = ku.fastag_id
WHERE al.access_result = 'granted' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY al.tag_id
ORDER BY granted_count DESC
LIMIT 10;

-- Most denied tags today
SELECT 
    al.tag_id,
    COUNT(*) as denied_count,
    al.reason
FROM access_logs al
WHERE al.access_result = 'denied' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY al.tag_id, al.reason
ORDER BY denied_count DESC
LIMIT 10;

-- 12. REASON ANALYSIS FOR DENIED ACCESS TODAY
-- =====================================================

-- Denial reasons today
SELECT 
    COALESCE(al.reason, 'No reason specified') as reason,
    COUNT(*) as denied_count
FROM access_logs al
WHERE al.access_result = 'denied' 
    AND DATE(al.timestamp) = DATE('now')
GROUP BY al.reason
ORDER BY denied_count DESC; 
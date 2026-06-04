-- 00013_cleanup_non_profile_user_tags.sql
-- Restrict profile tags to industry/occupation only (BR-U09).
-- Remove existing user_tags rows whose tag belongs to other categories.

DELETE FROM user_tags
 WHERE tag_id IN (
   SELECT id FROM tags WHERE category NOT IN ('industry', 'occupation')
 );

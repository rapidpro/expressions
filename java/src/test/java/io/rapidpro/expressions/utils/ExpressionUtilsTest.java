package io.rapidpro.expressions.utils;

import org.junit.Test;
import org.threeten.bp.Instant;
import org.threeten.bp.ZoneOffset;
import org.threeten.bp.ZonedDateTime;

import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

import static io.rapidpro.expressions.utils.ExpressionUtils.*;
import static org.hamcrest.Matchers.*;
import static org.junit.Assert.assertThat;

/**
 * Tests for {@link ExpressionUtils}
 */
public class ExpressionUtilsTest {

    @Test
    public void _slice() {
        assertThat(slice(Collections.emptyList(), null, null), empty());
        assertThat(slice(Arrays.asList(1, 2, 3, 4), 3, 2), empty());
        assertThat(slice(Arrays.asList(1, 2, 3, 4), 7, 9), empty());

        assertThat(slice(Arrays.asList(1, 2, 3, 4), null, null), contains(1, 2, 3, 4));
        assertThat(slice(Arrays.asList(1, 2, 3, 4), 1, null), contains(2, 3, 4));
        assertThat(slice(Arrays.asList(1, 2, 3, 4), 1, 3), contains(2, 3));
        assertThat(slice(Arrays.asList(1, 2, 3, 4), 1, -1), contains(2, 3));
        assertThat(slice(Arrays.asList(1, 2, 3, 4), -3, -1), contains(2, 3));
    }

    @Test
    public void _urlquote() {
        assertThat(urlquote(""), is(""));
        assertThat(urlquote("?!=Jow&Flow"), is("%3F%21%3DJow%26Flow"));
    }

    @Test
    public void _tokenize() {
        assertThat(tokenize("this is a sentence"), arrayContaining("this", "is", "a", "sentence"));
        assertThat(tokenize("  hey  \t@ there  "), arrayContaining("hey", "there"));
        assertThat(tokenize("واحد اثنين ثلاثة"), arrayContaining("واحد", "اثنين", "ثلاثة"));
    }

    @Test
    public void _parseJsonDate() {
        Instant val = ZonedDateTime.of(2014, 10, 3, 1, 41, 12, 790000000, ZoneOffset.UTC).toInstant();

        assertThat(parseJsonDate(null), is(nullValue()));
        assertThat(parseJsonDate("2014-10-03T01:41:12.790Z"), is(val));
    }

    @Test
    public void _formatJsonDate() {
        Instant val = ZonedDateTime.of(2014, 10, 3, 1, 41, 12, 790000000, ZoneOffset.UTC).toInstant();

        assertThat(formatJsonDate(null), is(nullValue()));
        assertThat(formatJsonDate(val), is("2014-10-03T01:41:12.790Z"));
    }

    @Test
    public void _toLowercaseKeys() {
        Map<String, String> map = new HashMap<>();
        map.put("FOO", "1");
        map.put("bAr", "2");

        assertThat(toLowerCaseKeys(map), allOf(hasEntry("foo", "1"), hasEntry("bar", "2")));
    }
}

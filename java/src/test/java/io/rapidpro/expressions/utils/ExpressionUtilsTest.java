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
        assertThat(tokenize(" one "), arrayContaining("one"));
        assertThat(tokenize("one   two three"), arrayContaining("one", "two", "three"));
        assertThat(tokenize("one.two.three"), arrayContaining("one", "two", "three"));
        assertThat(tokenize("O'Grady can't foo_bar"), arrayContaining("O'Grady", "can't", "foo_bar"));          // single quotes and underscores don't split tokens
        assertThat(tokenize("öne.βήταa.thé"), arrayContaining("öne", "βήταa", "thé"));                              // non-latin letters allowed in tokens
        assertThat(tokenize("واحد اثنين ثلاثة"), arrayContaining("واحد", "اثنين", "ثلاثة"));                           // RTL scripts
        assertThat(tokenize("  \t\none(two!*@three "), arrayContaining("one", "two", "three"));                      // other punctuation ignored
        assertThat(tokenize("spend$£€₠₣₪"), arrayContaining("spend", "$", "£", "€", "₠", "₣", "₪"));                 // currency symbols treated as individual tokens
        assertThat(tokenize("math+=×÷√∊"), arrayContaining("math", "+", "=", "×", "÷", "√", "∊"));                  // math symbols treated as individual tokens
        assertThat(tokenize("emoji😄🏥👪👰😟"), arrayContaining("emoji", "😄", "🏥", "👪", "👰", "😟"));  // emojis treated as individual tokens
        assertThat(tokenize("ℹ︎ ℹ️"), arrayContaining("ℹ", "ℹ"));                                                    // variation selectors ignored
    }

    @Test
    public void _formatIsoDate() {
        ZonedDateTime val1 = ZonedDateTime.of(2014, 10, 3, 1, 41, 12, 790000000, ZoneOffset.UTC);
        ZonedDateTime val2 = ZonedDateTime.of(2014, 10, 3, 1, 41, 12, 0, ZoneOffset.UTC);

        assertThat(formatIsoDate(null), is(nullValue()));
        assertThat(formatIsoDate(val1), is("2014-10-03T01:41:12.790000+00:00"));
        assertThat(formatIsoDate(val2), is("2014-10-03T01:41:12+00:00"));  // doesn't include microseconds if zero
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

    @Test
    public void _isEmojiChar() {
        assertThat(isSymbolChar('x'), is(false));
        assertThat(isSymbolChar('\u20A0'), is(true));
        assertThat(isSymbolChar(0x0001F300), is(true));
    }
}

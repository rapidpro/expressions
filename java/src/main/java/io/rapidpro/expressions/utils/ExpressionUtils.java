package io.rapidpro.expressions.utils;

import io.rapidpro.expressions.dates.DateStyle;
import org.apache.commons.lang3.ArrayUtils;
import org.threeten.bp.Instant;
import org.threeten.bp.LocalDateTime;
import org.threeten.bp.ZoneOffset;
import org.threeten.bp.format.DateTimeFormatter;

import java.io.UnsupportedEncodingException;
import java.math.BigDecimal;
import java.net.URLEncoder;
import java.util.*;

/**
 * Utility methods
 */
public final class ExpressionUtils {

    private ExpressionUtils() {}

    protected static DateTimeFormatter JSON_DATETIME_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'");

    /**
     * Slices a list, Python style
     * @param list the list
     * @param start the start index (null means the beginning of the list)
     * @param stop the stop index (null means the end of the list)
     * @return the slice
     */
    public static <T> List<T> slice(List<T> list, Integer start, Integer stop) {
        int size = list.size();

        if (start == null) {
            start = 0;
        } else if (start < 0) {
            start = size + start;
        }

        if (stop == null) {
            stop = size;
        } else if (stop < 0) {
            stop = size + stop;
        }

        if (start >= size || stop <= 0 || start >= stop) {
            return Collections.emptyList();
        }

        start = Math.max(0, start);
        stop = Math.min(size, stop);

        return list.subList(start, stop);
    }

    /**
     * Pow for two decimals
     */
    public static BigDecimal decimalPow(BigDecimal number, BigDecimal power) {
        return new BigDecimal(Math.pow(number.doubleValue(), power.doubleValue()));
    }

    /**
     * Encodes text for inclusion in a URL query string. Should be equivalent to Django's urlquote function.
     * @param text the text to encode
     * @return the encoded text
     */
    public static String urlquote(String text) {
        try {
            return URLEncoder.encode(text, "UTF-8").replace("+", "%20");
        } catch (UnsupportedEncodingException ex) {
            throw new RuntimeException(ex);
        }
    }

    /**
     * Gets a formatter for dates or datetimes
     * @param dateStyle whether parsing should be day-first or month-first
     * @param incTime whether to include time
     * @return the formatter
     */
    public static DateTimeFormatter getDateFormatter(DateStyle dateStyle, boolean incTime) {
        String format = dateStyle.equals(DateStyle.DAY_FIRST) ? "dd-MM-yyyy" : "MM-dd-yyyy";
        return DateTimeFormatter.ofPattern(incTime ? format + " HH:mm" : format);
    }

    /**
     * Replacement for Java 8's Map#getOrDefault(String, Object)
     */
    public static <K, V> V getOrDefault(Map<K, V> map, K key, V defaultValue) {
        return map.containsKey(key) ? map.get(key) : defaultValue;
    }

    /**
     * Tokenizes a string by splitting on non-word characters. This should be equivalent to splitting on \W+ in Python.
     * The meaning of \W is different in Android, Java 7, Java 8 hence the non-use of regular expressions.
     * @param text the input text
     * @return the string tokens
     */
    public static String[] tokenize(String text) {
        final int len = text.length();
        if (len == 0) {
            return ArrayUtils.EMPTY_STRING_ARRAY;
        }
        final List<String> list = new ArrayList<>();
        int i = 0, start = 0;
        boolean match = false;
        while (i < len) {
            int ch = text.codePointAt(i);
            if (!(Character.isDigit(ch) || ch == '_' || Character.isAlphabetic(ch))) {
                if (match) {
                    list.add(text.substring(start, i));
                    match = false;
                }
                start = ++i;
                continue;
            }
            match = true;
            i++;
        }
        if (match) {
            list.add(text.substring(start, i));
        }
        return list.toArray(new String[list.size()]);
    }

    /**
     * Formats a time instant as ISO8601 in UTC with millisecond precision, e.g. "2014-10-03T09:41:12.790Z"
     */
    public static String formatJsonDate(Instant value) {
        if (value == null) {
            return null;
        }
        return JSON_DATETIME_FORMAT.format(value.atOffset(ZoneOffset.UTC));
    }

    /**
     * Parses an ISO8601 formatted time instant from a string value
     */
    public static Instant parseJsonDate(String value) {
        if (value == null) {
            return null;
        }
        return LocalDateTime.parse(value, JSON_DATETIME_FORMAT).atOffset(ZoneOffset.UTC).toInstant();
    }

    /**
     * Returns a copy of the given map with lowercase keys
     * @param map the map to convert
     * @return copy of map with lowercase keys
     */
    public static <T> Map<String, T> toLowerCaseKeys(Map<String, T> map) {
        Map<String, T> res = new HashMap<>();
        for (Map.Entry<String, T> entry : map.entrySet()) {
            res.put(entry.getKey().toLowerCase(), entry.getValue());
        }
        return res;
    }
}

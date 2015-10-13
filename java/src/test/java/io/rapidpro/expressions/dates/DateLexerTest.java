package io.rapidpro.expressions.dates;

import org.junit.Test;

import static org.hamcrest.Matchers.contains;
import static org.hamcrest.Matchers.empty;
import static org.junit.Assert.assertThat;

/**
 * Test for {@link DateLexer}
 */
public class DateLexerTest {

    @Test
    public void tokenize() {
        DateLexer lexer = new DateLexer();

        assertThat(lexer.tokenize(""), empty());

        assertThat(lexer.tokenize("ab123cd"), contains(
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "ab", 0, 2),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "123", 2, 5),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "cd", 5, 7)
        ));

        assertThat(lexer.tokenize(" åb123d éf45-gh "), contains(
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "åb", 1, 3),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "123", 3, 6),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "d", 6, 7),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "éf", 8, 10),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "45", 10, 12),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "gh", 13, 15)
        ));

        assertThat(lexer.tokenize("12/5/15"), contains(
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "12", 0, 2),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "5", 3, 4),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "15", 5, 7)
        ));

        assertThat(lexer.tokenize("2015-10-13T12:31:30.123Z"), contains(
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "2015", 0, 4),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "10", 5, 7),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "13", 8, 10),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "T", 10, 11),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "12", 11, 13),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "31", 14, 16),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "30", 17, 19),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "123", 20, 23),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "Z", 23, 24)
        ));

        assertThat(lexer.tokenize("Today is the 13th of Oct 2015"), contains(
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "Today", 0, 5),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "is", 6, 8),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "the", 9, 12),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "13", 13, 15),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "th", 15, 17),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "of", 18, 20),
                new DateLexer.Token(DateLexer.Token.Type.ALPHABETIC, "Oct", 21, 24),
                new DateLexer.Token(DateLexer.Token.Type.NUMERIC, "2015", 25, 29)
        ));
    }
}

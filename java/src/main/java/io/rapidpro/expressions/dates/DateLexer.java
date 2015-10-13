package io.rapidpro.expressions.dates;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Lexer used by {@link DateParser}. Tokenizes input into sequences of digits or letters.
 */
public class DateLexer {

    protected enum State {
        IGNORED,
        NUMERIC_TOKEN,
        ALPHABETIC_TOKEN
    }

    public List<Token> tokenize(String text) {
        int length = text.length();
        if (length == 0) {
            return Collections.emptyList();
        }

        State state = State.IGNORED;
        Token.Type currentTokenType = null;
        int currentTokenStart = -1;
        final List<Token> tokens = new ArrayList<>();

        for (int pos = 0; pos < length; pos++) {
            int ch = text.codePointAt(pos);
            State prevState = state;

            if (Character.isAlphabetic(ch)) {
                state = State.ALPHABETIC_TOKEN;
            } else if (Character.isDigit(ch)) {
                state = State.NUMERIC_TOKEN;
            } else {
                state = State.IGNORED;
            }

            if (prevState != state) {
                // ending a token
                if (prevState != State.IGNORED) {
                    tokens.add(new Token(currentTokenType, text.substring(currentTokenStart, pos), currentTokenStart, pos));
                }

                // beginning a new token
                if (state != State.IGNORED) {
                    currentTokenType = state == State.NUMERIC_TOKEN ? Token.Type.NUMERIC : Token.Type.ALPHABETIC;
                    currentTokenStart = pos;
                }
            }
        }

        if (state != State.IGNORED) {
            tokens.add(new Token(currentTokenType, text.substring(currentTokenStart, length), currentTokenStart, length));
        }

        return tokens;
    }

    /**
     * A lexer token
     */
    public static class Token {

        public enum Type {
            NUMERIC,    // a sequence of digits
            ALPHABETIC  // a sequence of letters
        }

        protected Type m_type;

        protected String m_text;

        protected int m_start;

        protected int m_end;

        public Token(Type type, String text, int start, int end) {
            m_type = type;
            m_text = text;
            m_start = start;
            m_end = end;
        }

        public Type getType() {
            return m_type;
        }

        public String getText() {
            return m_text;
        }

        public int getStart() {
            return m_start;
        }

        public int getEnd() {
            return m_end;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;

            Token other = (Token) o;

            return m_type == other.m_type && m_text.equals(other.m_text) && m_start == other.m_start && m_end == other.m_end;
        }
    }
}

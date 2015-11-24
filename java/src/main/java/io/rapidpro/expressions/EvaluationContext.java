package io.rapidpro.expressions;

import com.google.gson.*;
import io.rapidpro.expressions.dates.DateParser;
import io.rapidpro.expressions.dates.DateStyle;
import io.rapidpro.expressions.utils.ExpressionUtils;
import org.threeten.bp.*;
import org.threeten.bp.format.DateTimeFormatter;

import java.lang.reflect.Type;
import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

/**
 * The evaluation context, i.e. date options and the variables accessible in an expression
 */
public class EvaluationContext {

    protected static Gson s_gson = new GsonBuilder()
                .registerTypeAdapter(EvaluationContext.class, new Deserializer())
                .create();

    protected Map<String, Object> m_variables;

    protected ZoneId m_timezone;

    protected DateStyle m_dateStyle;

    protected Instant m_now;

    public EvaluationContext() {
        this.m_variables = new HashMap<>();
        this.m_timezone = ZoneOffset.UTC;
        this.m_dateStyle = DateStyle.DAY_FIRST;
        this.m_now = Instant.now();
    }

    public EvaluationContext(Map<String, Object> variables, ZoneId timezone, DateStyle dateStyle) {
        this.m_variables = variables;
        this.m_timezone = timezone;
        this.m_dateStyle = dateStyle;
        this.m_now = Instant.now();
    }

    public EvaluationContext(Map<String, Object> variables, ZoneId timezone, DateStyle dateStyle, Instant now) {
        this.m_variables = variables;
        this.m_timezone = timezone;
        this.m_dateStyle = dateStyle;
        this.m_now = now;
    }

    public static EvaluationContext fromJson(String json) {
        return s_gson.fromJson(json, EvaluationContext.class);
    }

    public Map<String, Object> getVariables() {
        return m_variables;
    }

    /**
     * Returns a named variable, e.g. contact, contact.name
     * @param path the dot notation variable path
     * @return the variable value
     * @throws EvaluationError if variable is not defined
     */
    public Object resolveVariable(String path) {
        return resolveVariableInContainer(m_variables, path.toLowerCase(), path);
    }

    public void putVariable(String key, Object value) {
        m_variables.put(key, value);
    }

    public ZoneId getTimezone() {
        return m_timezone;
    }

    public DateStyle getDateStyle() {
        return m_dateStyle;
    }

    public void setDateStyle(DateStyle dateStyle) {
        m_dateStyle = dateStyle;
    }

    public Instant getNow() {
        return m_now;
    }

    public DateTimeFormatter getDateFormatter(boolean incTime) {
        return ExpressionUtils.getDateFormatter(m_dateStyle, incTime);
    }

    public DateParser getDateParser() {
        return new DateParser(LocalDate.now(), this.m_timezone, m_dateStyle);
    }

    private Object resolveVariableInContainer(Map<String, Object> container, String path, String originalPath) {
        String item, remainingPath;

        if (path.contains(".")) {
            String[] parts = path.split("\\.", 2);
            item = parts[0];
            remainingPath = parts[1];
        } else {
            item = path;
            remainingPath = null;
        }

        // copy of container with all lowercase keys
        container = ExpressionUtils.toLowerCaseKeys(container);

        if (!container.containsKey(item)) {
            throw new EvaluationError("Undefined variable: " + originalPath);
        }

        Object value = container.get(item);

        if (remainingPath != null && value != null) {
            if (!(value instanceof Map)) {
                throw new EvaluationError("Undefined variable: " + originalPath);
            }

            return resolveVariableInContainer((Map<String, Object>) value, remainingPath, originalPath);
        }
        else if (value instanceof Map) {
            return ExpressionUtils.renderDict((Map<String, Object>) value);
        } else {
            return value;
        }
    }

    /**
     * JSON de-serializer for evaluation contexts
     */
    public static class Deserializer implements JsonDeserializer<EvaluationContext> {
        @Override
        public EvaluationContext deserialize(JsonElement node, Type type, JsonDeserializationContext context) throws JsonParseException {
            JsonObject rootObj = node.getAsJsonObject();
            JsonObject varsObj = rootObj.get("variables").getAsJsonObject();
            ZoneId timezone = ZoneId.of(rootObj.get("timezone").getAsString());
            boolean dayFirst = rootObj.get("date_style").getAsString().equals("day_first");
            DateStyle dateStyle = dayFirst ? DateStyle.DAY_FIRST : DateStyle.MONTH_FIRST;
            Instant now;

            if (rootObj.has("now")) {
                now = ExpressionUtils.parseJsonDate(rootObj.get("now").getAsString());
            } else {
                now = Instant.now();
            }

            Map<String, Object> variables = new HashMap<>();
            for (Map.Entry<String, JsonElement> entry : varsObj.entrySet()) {
                variables.put(entry.getKey(), handleNode(entry.getValue(), Object.class, context));
            }

            return new EvaluationContext(variables, timezone, dateStyle, now);
        }

        public Object handleNode(JsonElement node, Type type, JsonDeserializationContext context) throws JsonParseException {
            if (node.isJsonNull()) {
                return null;
            }  else if (node.isJsonPrimitive()) {
                return handlePrimitive(node.getAsJsonPrimitive());
            } else if (node.isJsonArray()) {
                return handleArray(node.getAsJsonArray(), context);
            } else {
                return handleObject(node.getAsJsonObject(), context);
            }
        }

        private Object handlePrimitive(JsonPrimitive node) {
            if (node.isBoolean()) {
                return node.getAsBoolean();
            } else if (node.isString()) {
                return node.getAsString();
            } else {
                BigDecimal decimal = node.getAsBigDecimal();
                try {
                    // return numbers as integers if possible
                    return decimal.intValueExact();
                }
                catch (ArithmeticException e) {
                    return decimal;
                }
            }
        }

        private Object handleArray(JsonArray node, JsonDeserializationContext context) {
            Object[] array = new Object[node.size()];
            for (int i = 0; i < array.length; i++) {
                array[i] = handleNode(node.get(i), Object.class, context);
            }
            return array;
        }

        private Object handleObject(JsonObject json, JsonDeserializationContext context) {
            Map<String, Object> map = new HashMap<>();

            for (Map.Entry<String, JsonElement> entry : json.entrySet()) {
                map.put(entry.getKey(), handleNode(entry.getValue(), Object.class, context));
            }
            return map;
        }
    }
}

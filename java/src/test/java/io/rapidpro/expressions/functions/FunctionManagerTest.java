package io.rapidpro.expressions.functions;

import io.rapidpro.expressions.EvaluationContext;
import io.rapidpro.expressions.EvaluationError;
import io.rapidpro.expressions.functions.annotations.IntegerDefault;
import org.junit.Before;
import org.junit.Test;

import java.util.Arrays;
import java.util.List;

import static org.hamcrest.Matchers.is;
import static org.hamcrest.Matchers.nullValue;
import static org.junit.Assert.assertThat;

/**
 * Tests for {@link FunctionManager}
 */
public class FunctionManagerTest {

    private EvaluationContext m_context;

    @Before
    public void setup() {
        m_context = new EvaluationContext();
    }

    @Test
    public void invokeFunction() {
        FunctionManager manager = new FunctionManager();
        manager.addLibrary(TestFunctions.class);

        assertThat(manager.invokeFunction(m_context, "foo", Arrays.<Object>asList(12)), is((Object) 24));
        assertThat(manager.invokeFunction(m_context, "FOO", Arrays.<Object>asList(12)), is((Object) 24));
        assertThat(manager.invokeFunction(m_context, "bar", Arrays.<Object>asList(12, 5)), is((Object) 17));
        assertThat(manager.invokeFunction(m_context, "bar", Arrays.<Object>asList(12)), is((Object) 14));
        assertThat(manager.invokeFunction(m_context, "doh", Arrays.<Object>asList(12, 1, 2, 3)), is((Object) 36));
    }

    @Test(expected = EvaluationError.class)
    public void invokeFunction_nonPublic() {
        FunctionManager manager = new FunctionManager();
        manager.addLibrary(TestFunctions.class);
        manager.invokeFunction(m_context, "zed", Arrays.<Object>asList(12));
    }

    @Test(expected = EvaluationError.class)
    public void invokeFunction_nonRecognizedDataType() {
        FunctionManager manager = new FunctionManager();
        manager.addLibrary(TestFunctions.class);
        manager.invokeFunction(m_context, "foo", Arrays.<Object>asList(this));
    }

    @Test
    public void buildListing() {
        FunctionManager manager = new FunctionManager();
        manager.addLibrary(TestFunctions.class);
        List<FunctionManager.FunctionDescriptor> listing = manager.buildListing();

        assertThat(listing.get(0).getName(), is("BAR"));
    }

    public static class TestFunctions {

        public static int foo(EvaluationContext ctx, int a) {
            return a * 2;
        }

        public static int _bar(EvaluationContext ctx, int a, @IntegerDefault(2) int b) {
            return a + b;
        }

        public static int doh(int a, Object... args) {
            return args.length * a;
        }

        private static int zed(int a) {
            return a / 2;
        }
    }
}

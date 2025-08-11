package dog.poochie.camaragateway;

import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

@Component
public class CheckScopeGatewayFilterFactory extends AbstractGatewayFilterFactory<CheckScopeGatewayFilterFactory.Config> {

    public CheckScopeGatewayFilterFactory() {
        super(Config.class);
    }

    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> exchange.getPrincipal()
                .flatMap(principal -> {
                    if (principal instanceof JwtAuthenticationToken) {
                        JwtAuthenticationToken token = (JwtAuthenticationToken) principal;
                        boolean hasScope = token.getAuthorities().stream()
                                .map(GrantedAuthority::getAuthority)
                                .anyMatch(authority -> authority.equals("SCOPE_" + config.getScope()));

                        if (hasScope) {
                            return chain.filter(exchange);
                        }
                    }
                    // If scope is not present, return 403 Forbidden
                    exchange.getResponse().setStatusCode(HttpStatus.FORBIDDEN);
                    return exchange.getResponse().setComplete();
                });
    }

    public static class Config {
        private String scope;

        public String getScope() {
            return scope;
        }

        public void setScope(String scope) {
            this.scope = scope;
        }
    }
}
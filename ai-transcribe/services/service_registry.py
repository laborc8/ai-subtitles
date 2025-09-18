from typing import Dict, Type
from .base_service import BaseService, ServiceType

class ServiceRegistry:
    """Registry for managing different WebSocket services"""
    
    def __init__(self):
        self._services: Dict[ServiceType, BaseService] = {}
        self._service_classes: Dict[ServiceType, Type[BaseService]] = {}
        
    def register_service(self, service_type: ServiceType, service_class: Type[BaseService]):
        """Register a service class"""
        self._service_classes[service_type] = service_class
    
    def get_service(self, service_type: ServiceType) -> BaseService:
        """Get or create service instance"""
        if service_type not in self._services:
            service_class = self._service_classes.get(service_type)
            if service_class:
                self._services[service_type] = service_class()
            else:
                raise ValueError(f"Service type {service_type} not registered")
        
        return self._services[service_type]
    
    def cleanup_client(self, client_id: str):
        """Cleanup all services for a client"""
        for service in self._services.values():
            service.cleanup(client_id)
    
    def get_supported_services(self) -> list:
        """Get list of supported service types"""
        return list(self._service_classes.keys())

# Global service registry
service_registry = ServiceRegistry() 
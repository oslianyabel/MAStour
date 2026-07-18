from django import forms

from tours.models import Reservation, Slot


class ReservationForm(forms.ModelForm):
    """Client-facing reservation form for a specific slot."""

    class Meta:
        model = Reservation
        fields = [
            'adults_count',
            'children_count',
            'representative_name',
            'representative_phone',
            'address',
        ]
        widgets = {
            'adults_count': forms.NumberInput(attrs={'min': 1, 'inputmode': 'numeric'}),
            'children_count': forms.NumberInput(attrs={'min': 0, 'inputmode': 'numeric'}),
            'representative_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'representative_phone': forms.TextInput(
                attrs={'autocomplete': 'tel', 'inputmode': 'tel', 'placeholder': '+53 5xxxxxxx'}
            ),
            'address': forms.TextInput(attrs={'autocomplete': 'street-address'}),
        }

    def __init__(self, slot: Slot, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.slot = slot

    def clean(self) -> dict:
        cleaned_data = super().clean()
        adults_count: int = cleaned_data.get('adults_count') or 0
        children_count: int = cleaned_data.get('children_count') or 0
        requested_seats = adults_count + children_count
        if requested_seats < 1:
            raise forms.ValidationError('Debe reservar al menos una plaza.')
        seats_available = self.slot.seats_available
        if requested_seats > seats_available:
            raise forms.ValidationError(
                f'No hay capacidad suficiente: quedan {seats_available} plazas disponibles.'
            )
        return cleaned_data

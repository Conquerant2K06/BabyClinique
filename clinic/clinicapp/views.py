from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, View, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout as auth_logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.decorators import login_required
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review, Service

# Vue pour la liste des catégories (page d'accueil)
class CategoryListView(ListView):
    model = Category
    template_name = 'index.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'index'
        return context

# Vue pour la liste des produits par catégorie
class ProductListView(ListView):
    model = Product
    template_name = 'produit.html'
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'products'  
        return context

# Vue pour les détails d'un produit
class ProductDetailView(DetailView):
    model = Product
    template_name = 'produit-detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all()
        context['active_page'] = 'produits'  
        return context

# Vue pour ajouter un produit au panier
class AddToCartView(LoginRequiredMixin, View):
    def post(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        
        try:
            quantity = int(request.POST.get('quantity'))
            if quantity < 1:
                quantity = 1
        except (TypeError, ValueError):
            quantity = 1
        
        print("Quantité reçue depuis POST:", quantity)

        # Vérifier le stock
        if quantity > product.stock:
            messages.error(request, f"Stock insuffisant pour {product.name}.")
            return redirect('product_detail', slug=product.slug)

        # Récupérer ou créer le panier de l'utilisateur
        cart, created = Cart.objects.get_or_create(user=request.user)

        # ✅ Correction ici : passer quantity dans defaults
        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not item_created:
            cart_item.quantity += quantity
            cart_item.save()  # Ne pas oublier d’enregistrer la modification

        messages.success(request, f"{product.name} ajouté au panier.")
        return redirect('cart_detail')


# Vue pour afficher le panier
class CartView(View):
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product')
        context_object_name = 'Cart'
        total = sum(item.get_total_price() for item in items)
        return render(request, 'cart-detail.html', {
            'cart': cart,
            'items': items,
            'total': total
        })
         

from django.shortcuts import render, redirect
from django.contrib.auth import login  # Ajout pour connecter automatiquement
from django.contrib import messages
from .forms import CustomUserCreationForm  # Import de votre formulaire personnalisé

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Sauvegarder et récupérer l'utilisateur créé
            username = form.cleaned_data.get('username')
            
            # Message de succès personnalisé
            messages.success(request, f'Compte créé avec succès pour {username} ! Vous êtes maintenant connecté.')
            
            # Connecter automatiquement l'utilisateur après inscription (optionnel)
            login(request, user)
            
            return redirect('login')  # ou 'dashboard' si vous voulez rediriger vers le tableau de bord
        else:
            # Message d'erreur si le formulaire n'est pas valide
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


# Vue pour supprimer un article du panier
from django.shortcuts import render

class RemoveFromCartView(LoginRequiredMixin, View):
    def get(self, request, item_id):
       item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
       return render(request, 'cart-remove.html.html', {'item': item})

    def post(self, request, item_id):
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        messages.success(request, "Article retiré du panier.")
        return redirect('cart_detail')

from django.db.models import Sum, F
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal
from .models import Cart, CartItem, Order, OrderItem

class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        
        # Préparer les données du panier avec les calculs
        cart_items = []
        total_cart = Decimal('0.00')
        
        for item in cart.items.all():
            item_total = item.quantity * item.product.price
            cart_items.append({
                'product': item.product,
                'quantity': item.quantity,
                'unit_price': item.product.price,
                'total_price': item_total
            })
            total_cart += item_total
        
        requires_prescription = any(item.product.requires_prescription for item in cart.items.all())
        
        # Récupérer les choix de paiement depuis le modèle
        payment_choices = Order.PAYMENT_METHOD_CHOICES
        
        return render(request, 'checkout.html', {
            'cart': cart,
            'cart_items': cart_items,
            'total_cart': total_cart,
            'active_page': 'checkout',
            'requires_prescription': requires_prescription,
            'payment_choices': payment_choices
        })

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        shipping_address = request.POST.get('shipping_address')
        prescription_file = request.FILES.get('prescription_file')
        payment_method = request.POST.get('payment_method')

        # Vérifier si une ordonnance est requise
        requires_prescription = any(item.product.requires_prescription for item in cart.items.all())
        
        # Validation des champs requis
        errors = []
        
        if not shipping_address:
            errors.append("L'adresse de livraison est requise.")
        
        if not payment_method:
            errors.append("Veuillez sélectionner un mode de paiement.")
        
        if requires_prescription and not prescription_file:
            errors.append("Une ordonnance est requise pour certains produits.")
        
        # Vérifier que le mode de paiement est valide
        valid_payment_methods = [choice[0] for choice in Order.PAYMENT_METHOD_CHOICES]
        if payment_method and payment_method not in valid_payment_methods:
            errors.append("Mode de paiement invalide.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            
            # Recalculer les données pour le rendu en cas d'erreur
            cart_items = []
            total_cart = Decimal('0.00')
            
            for item in cart.items.all():
                item_total = item.quantity * item.product.price
                cart_items.append({
                    'product': item.product,
                    'quantity': item.quantity,
                    'unit_price': item.product.price,
                    'total_price': item_total
                })
                total_cart += item_total
            
            payment_choices = Order.PAYMENT_METHOD_CHOICES
            
            return render(request, 'checkout.html', {
                'cart': cart,
                'cart_items': cart_items,
                'total_cart': total_cart,
                'active_page': 'checkout',
                'requires_prescription': requires_prescription,
                'payment_choices': payment_choices
            })

        # Calculer le prix total correct (quantité * prix)
        total_price = Decimal('0.00')
        for item in cart.items.all():
            total_price += item.quantity * item.product.price

        # Créer la commande avec le mode de paiement
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            shipping_address=shipping_address,
            prescription_file=prescription_file,
            payment_method=payment_method
        )

        # Créer les articles de la commande
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        # Vider le panier
        cart.items.all().delete()
        
        # Message de succès personnalisé selon le mode de paiement
        payment_method_display = dict(Order.PAYMENT_METHOD_CHOICES).get(payment_method, payment_method)
        messages.success(request, f"Commande passée avec succès. Mode de paiement : {payment_method_display}")
        
        return redirect('order_confirmation', order_id=order.id)
    

# Vue pour confirmer la commande
class OrderConfirmationView(LoginRequiredMixin, View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        return render(request, 'order_confirmation.html', {'order': order, 'active_page': 'order_confirmation'})

# Vue pour ajouter un avis sur un produit
class AddReviewView(LoginRequiredMixin, CreateView):
    model = Review
    fields = ['rating', 'comment']
    template_name = 'pharmacy/add_review.html'

    def form_valid(self, form):
        product = get_object_or_404(Product, slug=self.kwargs['slug'])
        form.instance.user = self.request.user
        form.instance.product = product
        try:
            return super().form_valid(form)
        except ValidationError:
            messages.error(self.request, "Vous avez déjà laissé un avis sur ce produit.")
            return redirect('produit-detail', slug=product.slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'services'  # Avis lié aux produits, donc "services"
        return context

    def get_success_url(self):
        return reverse_lazy('produit-detail', kwargs={'slug': self.kwargs['slug']})

# Formulaire pour la page Contact
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import ContactForm

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Traitez les données du formulaire ici
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            # Envoyez un email, enregistrez dans la base de données, etc.
            # Par exemple, envoyez un email :
            # send_mail(subject, message, email, ['admin@example.com'])

            return HttpResponse('Merci pour votre message!')
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})


# views.py
from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Category

def medication_list(request):
    """Vue pour afficher la liste des médicaments avec recherche"""
    
    # Récupérer tous les produits
    products = Product.objects.all().select_related('category')
    
    # Récupérer toutes les catégories pour le filtre
    categories = Category.objects.all()
    
    # Paramètres de recherche
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    needs_prescription = request.GET.get('prescription', '')
    no_prescription = request.GET.get('no_prescription', '')
    
    # Filtrage par terme de recherche
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Filtrage par catégorie
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filtrage par ordonnance
    if needs_prescription:
        products = products.filter(requires_prescription=True)
    elif no_prescription:
        products = products.filter(requires_prescription=False)
    
    # Tri par nom
    products = products.order_by('category__name', 'name')
    
    # Pagination (optionnel)
    paginator = Paginator(products, 12)  # 12 produits par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': products,  # ou page_obj si vous utilisez la pagination
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'needs_prescription': needs_prescription,
        'no_prescription': no_prescription,
        # 'page_obj': page_obj,  # si vous utilisez la pagination
    }
    
    return render(request, 'medications/medication_list.html', context)


# Alternative avec recherche AJAX (optionnel)
from django.http import JsonResponse
from django.template.loader import render_to_string

def medication_search_ajax(request):
    """Vue AJAX pour la recherche en temps réel"""
    
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Requête non autorisée'}, status=400)
    
    search_query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    needs_prescription = request.GET.get('prescription', '')
    no_prescription = request.GET.get('no_prescription', '')
    
    products = Product.objects.all().select_related('category')
    
    # Appliquer les filtres
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if needs_prescription:
        products = products.filter(requires_prescription=True)
    elif no_prescription:
        products = products.filter(requires_prescription=False)
    
    products = products.order_by('category__name', 'name')
    
    # Rendu du template partiel
    html = render_to_string('medications/medication_cards.html', {
        'products': products,
    })
    
    return JsonResponse({
        'html': html,
        'count': products.count(),
        'success': True
    })

# Formulaire pour la page Appointment
class AppointmentForm(forms.Form):
    name = forms.CharField(max_length=100, label="Votre nom")
    email = forms.EmailField(label="Votre email")
    phone = forms.CharField(max_length=20, label="Numéro de téléphone", required=False)
    date = forms.DateField(label="Date souhaitée", widget=forms.DateInput(attrs={'type': 'date'}))
    message = forms.CharField(widget=forms.Textarea, label="Détails", required=False)

# Vue pour la page About
class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'about'
        return context

# Vue pour la page Team
class TeamView(TemplateView):
    template_name = 'team.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'team'
        return context

# Vue pour la page Feature
class FeatureView(TemplateView):
    template_name = 'feature.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'feature'
        return context

# Vue pour la page Testimonial
class TestimonialView(TemplateView):
    template_name = 'testimonial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'testimonial'
        return context

# Vue pour la page Contact
class ContactView(FormView):
    template_name = 'contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact')

    def form_valid(self, form):
        messages.success(self.request, "Merci pour votre message ! Nous vous répondrons bientôt.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'contact'
        return context

# Vue pour la page Appointment
class AppointmentView(FormView):
    template_name = 'appointment.html'
    form_class = AppointmentForm
    success_url = reverse_lazy('appointment')

    def form_valid(self, form):
        messages.success(self.request, "Votre demande de rendez-vous a été enregistrée !")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_page'] = 'appointment'
        return context

# Vue pour la page 404 personnalisée
def custom_404(request):
    return render(request, '404.html', {'active_page': '404'})



from django.core.mail import send_mail
from django.core.mail.message import EmailMessage
from smtplib import SMTPException
import logging

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                
                # Tentative d'envoi d'email avec gestion d'erreur
                try:
                    send_mail(
                        'Connexion réussie',
                        f'Bonjour {username}, vous venez de vous connecter à votre compte.',
                        'angeemmanuel2k06@gmail.com',
                        [user.email],
                        fail_silently=False,
                    )
                except SMTPException as e:
                    logger.error(f"Erreur lors de l'envoi d'email de connexion: {e}")
                    # Optionnel: ajouter un message d'information pour l'utilisateur
                    messages.info(request, "Connexion réussie. Email de notification non envoyé.")
                except Exception as e:
                    logger.error(f"Erreur inattendue lors de l'envoi d'email: {e}")
                
                return redirect('index')
            else:
                messages.error(request, "Vous n'avez pas les droits d'accès nécessaires.")
                return render(request, 'registration/login.html', {'active_page': 'login'})
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
            
            User = get_user_model()
            try:
                user_obj = User.objects.get(username=username)
                # Tentative d'envoi d'email avec gestion d'erreur
                try:
                    send_mail(
                        'Tentative de connexion échouée',
                        'Une tentative de connexion à votre compte a échoué.',
                        'angeemmanuel2k06@gmail.com',
                        [user_obj.email],
                        fail_silently=False,
                    )
                except SMTPException as e:
                    logger.error(f"Erreur lors de l'envoi d'email d'échec de connexion: {e}")
                except Exception as e:
                    logger.error(f"Erreur inattendue lors de l'envoi d'email: {e}")
            except User.DoesNotExist:
                pass
            
            return render(request, 'registration/login.html', {'active_page': 'login'})
    
    return render(request, 'registration/login.html', {'active_page': 'login'})


# Vue pour la déconnexion
@require_http_methods(['GET', 'POST'])
@never_cache
def logout_view(request):
    """
    Log out the user and render the logged out template.
    """
    if request.method == 'POST':
        @method_decorator(csrf_protect)
        def post_handler():
            auth_logout(request)
            return render(request, 'logout.html', {'active_page': 'logout'})
        return post_handler()
    
    auth_logout(request)
    return render(request, 'logout.html', {'active_page': 'logout'})

# Vue pour les services
@require_http_methods(['GET'])
def service_view(request):
    """
    Affiche la liste des services médicaux dynamiques.
    """
    services = Service.objects.all()
    return render(request, 'services.html', {'services': services, 'active_page': 'services'})

# Vue pour les détails d'un service
def service_detail_view(request, service_id):
    """
    Affiche les détails d'un service.
    """
    service = get_object_or_404(Service, id=service_id)
    services = Service.objects.all()  # Pour le footer
    return render(request, 'service_detail.html', {'service': service, 'services': services, 'active_page': 'services'})

